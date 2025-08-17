#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const chalk = require('chalk');
const prompts = require('prompts');
const ora = require('ora');
const { execSync } = require('child_process');

const BANNER = `
╔═══════════════════════════════════════════════════╗
║                                                   ║
║   🧠 Claude Code Subagent Memory System 🧠       ║
║                                                   ║
║   Persistent memory for intelligent subagents    ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
`;

async function checkPython() {
  // Check if Python 3 is available
  try {
    const version = execSync('python3 --version', { encoding: 'utf8' }).trim();
    return { available: true, version };
  } catch (e) {
    try {
      const version = execSync('python --version', { encoding: 'utf8' }).trim();
      if (version.includes('Python 3')) {
        return { available: true, version, command: 'python' };
      }
    } catch {}
    return { available: false };
  }
}

async function setupMCPServer(claudeDir, installType, spinner) {
  const mcpDir = path.join(claudeDir, 'mcp', 'agent-messaging');
  
  // Check Python availability
  spinner.text = 'Checking Python installation...';
  const pythonCheck = await checkPython();
  
  if (!pythonCheck.available) {
    console.log(chalk.yellow('\n⚠️  Python 3 not found. MCP server requires Python 3.8+'));
    console.log(chalk.gray('   The memory system will work, but agent messaging will be unavailable.'));
    console.log(chalk.gray('   Install Python 3 and re-run the installer to enable messaging.\n'));
    return false;
  }
  
  const pythonCmd = pythonCheck.command || 'python3';
  
  try {
    // Create virtual environment
    spinner.text = 'Setting up MCP server virtual environment...';
    execSync(`${pythonCmd} -m venv venv`, { 
      cwd: mcpDir,
      stdio: 'ignore'
    });
    
    // Install dependencies
    spinner.text = 'Installing MCP server dependencies...';
    const pipCmd = process.platform === 'win32' 
      ? path.join(mcpDir, 'venv', 'Scripts', 'pip')
      : path.join(mcpDir, 'venv', 'bin', 'pip');
    
    // Try to upgrade pip, but don't fail if it doesn't work
    try {
      execSync(`${pipCmd} install --upgrade pip`, { 
        cwd: mcpDir,
        stdio: 'ignore'
      });
    } catch (e) {
      // Pip upgrade failed, but continue with existing pip
    }
    
    // Install MCP requirements
    try {
      execSync(`${pipCmd} install -r requirements.txt`, {
        cwd: mcpDir,
        stdio: 'ignore'
      });
    } catch (e) {
      // Installation might have had warnings but still worked
    }
    
    // Verify setup by checking if venv was created successfully
    const venvPath = path.join(mcpDir, 'venv');
    const pipPath = process.platform === 'win32' 
      ? path.join(venvPath, 'Scripts', 'pip')
      : path.join(venvPath, 'bin', 'pip');
    
    // If venv and pip exist, consider it successful
    if (fs.existsSync(venvPath) && fs.existsSync(pipPath)) {
      return true;
    }
    return false;
  } catch (error) {
    console.log(chalk.yellow('\n⚠️  MCP server setup encountered issues:', error.message));
    console.log(chalk.gray('   The memory system will work, but agent messaging may be unavailable.'));
    return false;
  }
}

async function configureMCPProject(claudeDir, mcpEnabled) {
  // Configure project-level MCP in PROJECT_ROOT/.mcp.json (not in .claude/)
  if (!mcpEnabled) return;
  
  const mcpConfigPath = '.mcp.json';  // Project root, not in .claude
  let mcpConfig = {};
  
  // Load existing .mcp.json if it exists
  if (fs.existsSync(mcpConfigPath)) {
    try {
      mcpConfig = await fs.readJson(mcpConfigPath);
    } catch (e) {
      mcpConfig = {};
    }
  }
  
  // Initialize mcpServers if needed
  if (!mcpConfig.mcpServers) {
    mcpConfig.mcpServers = {};
  }
  
  // Add agent-messaging server with paths relative to project root
  const pythonExecutable = process.platform === 'win32' 
    ? path.join('.claude', 'mcp', 'agent-messaging', 'venv', 'Scripts', 'python')
    : path.join('.claude', 'mcp', 'agent-messaging', 'venv', 'bin', 'python');
  
  const mcpServerPath = path.join('.claude', 'mcp', 'agent-messaging', 'server.py');
  const messagesDir = path.join('.claude', 'messages');
  
  mcpConfig.mcpServers['agent-messaging'] = {
    command: pythonExecutable,
    args: [mcpServerPath],
    env: {
      MESSAGES_DIR: messagesDir
    }
  };
  
  // Save .mcp.json in project root
  await fs.writeJson(mcpConfigPath, mcpConfig, { spaces: 2 });
}

async function configureSettings(claudeDir, installType, mcpEnabled = false) {
  // IMPORTANT: settings.json/settings.local.json is NOT included in template
  // It must be generated fresh for each installation to avoid hardcoded paths
  const settingsFile = installType === 'global' ? 'settings.json' : 'settings.local.json';
  const settingsPath = path.join(claudeDir, settingsFile);
  
  let settings = {};
  
  // Load existing settings if they exist
  if (fs.existsSync(settingsPath)) {
    try {
      settings = await fs.readJson(settingsPath);
    } catch (e) {
      // If we can't parse it, start fresh
      settings = {};
    }
  }
  
  // Initialize hooks object if it doesn't exist
  if (!settings.hooks) {
    settings.hooks = {};
  }
  
  // Configure hook paths based on installation type
  const hookPrefix = installType === 'global' 
    ? `python3 ${process.env.HOME}/.claude/hooks`
    : 'python3 $CLAUDE_PROJECT_DIR/.claude/hooks';
  
  // Add SessionStart hook for TRD protocol
  if (!settings.hooks.SessionStart) {
    settings.hooks.SessionStart = [];
  }
  
  // Check if hook already exists
  const sessionStartExists = settings.hooks.SessionStart.some(h => 
    h.hooks && h.hooks.some(hook => 
      hook.command && hook.command.includes('initialize_agent_system.py')
    )
  );
  
  if (!sessionStartExists) {
    settings.hooks.SessionStart.push({
      hooks: [{
        type: 'command',
        command: `${hookPrefix}/initialize_agent_system.py`
      }]
    });
  }
  
  // Add PreToolUse hook for context loading
  if (!settings.hooks.PreToolUse) {
    settings.hooks.PreToolUse = [];
  }
  
  const preToolUseExists = settings.hooks.PreToolUse.some(h => 
    h.matcher === 'Task' && h.hooks && h.hooks.some(hook => 
      hook.command && hook.command.includes('context_cache_checker.py')
    )
  );
  
  if (!preToolUseExists) {
    settings.hooks.PreToolUse.push({
      matcher: 'Task',
      hooks: [{
        type: 'command',
        command: `${hookPrefix}/context_cache_checker.py`
      }]
    });
  }
  
  // Add SubagentStop hook for memory processing
  if (!settings.hooks.SubagentStop) {
    settings.hooks.SubagentStop = [];
  }
  
  const subagentStopExists = settings.hooks.SubagentStop.some(h => 
    h.hooks && h.hooks.some(hook => 
      hook.command && hook.command.includes('subagent_memory_analyzer.py')
    )
  );
  
  if (!subagentStopExists) {
    settings.hooks.SubagentStop.push({
      hooks: [{
        type: 'command',
        command: `${hookPrefix}/subagent_memory_analyzer.py`,
        timeout: 300
      }]
    });
  }
  
  // Configure permissions
  if (!settings.permissions) {
    settings.permissions = { allow: [], block: [] };
  }
  
  const memoryPermissions = installType === 'global' 
    ? [
        'Bash(mkdir:*)',
        'Bash(claude-memory:*)',
        'Bash(ls:*)',
        'Bash(cat:*)',
        'Bash(rm:*)',
        'Write(~/.claude/memory/**)',
        'Edit(~/.claude/memory/**)',
        'Read(~/.claude/memory/**)',
        'Write(~/.claude/cache/**)',
        'Edit(~/.claude/cache/**)',
        'Read(~/.claude/cache/**)'
      ]
    : [
        'Bash(mkdir:*)',
        'Bash(claude-memory:*)',
        'Bash(./claude-memory:*)',
        'Bash(ls:*)',
        'Bash(cat:*)',
        'Bash(rm:*)',
        'Write(.claude/memory/**)',
        'Edit(.claude/memory/**)',
        'Read(.claude/memory/**)',
        'Write(.claude/cache/**)',
        'Edit(.claude/cache/**)',
        'Read(.claude/cache/**)'
      ];
  
  // Add memory-manager specific permissions
  const memoryManagerPermissions = [
    'Task(memory-manager)',
    'Bash(grep:*)'
  ];
  
  // Merge permissions (avoiding duplicates)
  const allPermissions = [...memoryPermissions, ...memoryManagerPermissions];
  for (const perm of allPermissions) {
    if (!settings.permissions.allow.includes(perm)) {
      settings.permissions.allow.push(perm);
    }
  }
  
  // Add MCP server configuration if enabled (only for global install)
  if (mcpEnabled && installType === 'global') {
    if (!settings.mcpServers) {
      settings.mcpServers = {};
    }
    
    // Use venv Python for global install too
    const pythonExecutable = process.platform === 'win32'
      ? path.join(process.env.HOME, '.claude', 'mcp', 'agent-messaging', 'venv', 'Scripts', 'python')
      : path.join(process.env.HOME, '.claude', 'mcp', 'agent-messaging', 'venv', 'bin', 'python');
    
    const mcpServerPath = path.join(process.env.HOME, '.claude', 'mcp', 'agent-messaging', 'server.py');
    const messagesDir = path.join(process.env.HOME, '.claude', 'messages');
    
    settings.mcpServers['agent-messaging'] = {
      command: pythonExecutable,
      args: [mcpServerPath],
      env: {
        MESSAGES_DIR: messagesDir
      }
    };
  }
  
  // Save updated settings
  await fs.writeJson(settingsPath, settings, { spaces: 2 });
}

async function main() {
  console.log(chalk.cyan(BANNER));
  console.log('This installer will set up persistent memory for your Claude Code subagents.\n');
  console.log(chalk.gray('Installing in current project (.claude directory)\n'));

  // Default to project installation (no prompt)
  const response = { installType: 'project' };
  const claudeDir = '.claude';

  // Check for existing installation
  if (fs.existsSync(path.join(claudeDir, 'memory'))) {
    const overwrite = await prompts({
      type: 'confirm',
      name: 'value',
      message: chalk.yellow('⚠️  Memory system already exists. Overwrite?'),
      initial: false
    });

    if (!overwrite.value) {
      // Ask if they want to update instead
      const update = await prompts({
        type: 'confirm',
        name: 'value',
        message: 'Would you like to update the existing installation instead?',
        initial: true
      });

      if (!update.value) {
        console.log(chalk.red('\n✖ Installation cancelled'));
        process.exit(1);
      }
      // Continue with update mode
      console.log(chalk.blue('\n📦 Updating existing installation...'));
    }
  }

  const spinner = ora('Installing memory system...').start();

  try {
    // Step 1: Create directory structure
    spinner.text = 'Creating directory structure...';
    const dirs = [
      'agents',
      'commands', 
      'hooks',
      'scripts',
      'memory/manager',
      'memory/agents',
      'memory/team',
      'memory/project',
      'cache'
    ];

    for (const dir of dirs) {
      await fs.ensureDir(path.join(claudeDir, dir));
    }

    // Step 2: Copy template files
    spinner.text = 'Copying memory system files...';
    const templateDir = path.join(__dirname, '..', 'template', '.claude');
    
    // Copy all .claude template files
    await fs.copy(templateDir, claudeDir, {
      overwrite: true,
      errorOnExist: false
    });

    // Step 3: Copy and setup claude-memory wrapper
    spinner.text = 'Setting up claude-memory wrapper...';
    const wrapperSource = path.join(__dirname, '..', 'template', 'claude-memory');
    let wrapperPath;
    
    if (response.installType === 'project') {
      // For project install, copy wrapper to project root
      wrapperPath = './claude-memory';
      await fs.copy(wrapperSource, wrapperPath);
      fs.chmodSync(wrapperPath, '755');
    } else {
      // For global install, copy to ~/.local/bin
      const binDir = path.join(process.env.HOME, '.local', 'bin');
      await fs.ensureDir(binDir);
      wrapperPath = path.join(binDir, 'claude-memory');
      await fs.copy(wrapperSource, wrapperPath);
      fs.chmodSync(wrapperPath, '755');
    }

    // Step 4: Make other scripts executable
    spinner.text = 'Setting up executables...';
    const executableFiles = [
      'scripts/memory-commands.sh',
      'hooks/initialize_agent_system.py',
      'hooks/subagent_memory_analyzer.py',
      'hooks/context_cache_checker.py'
    ];

    for (const file of executableFiles) {
      const filePath = path.join(claudeDir, file);
      if (fs.existsSync(filePath)) {
        fs.chmodSync(filePath, '755');
      }
    }

    // Step 5: Setup MCP server for agent messaging (optional)
    spinner.text = 'Setting up agent messaging server...';
    let mcpEnabled = false;
    
    // Check if MCP directory exists (it should from template copy)
    const mcpDir = path.join(claudeDir, 'mcp', 'agent-messaging');
    if (fs.existsSync(mcpDir)) {
      mcpEnabled = await setupMCPServer(claudeDir, response.installType, spinner);
      
      // Always create messages directory (even if MCP setup had issues)
      const messagesDir = path.join(claudeDir, 'messages');
      await fs.ensureDir(messagesDir);
      await fs.ensureDir(path.join(messagesDir, 'archive'));
    }
    
    // Step 6: Configure settings.json with hooks, permissions, and MCP
    spinner.text = 'Configuring hooks, permissions, and MCP...';
    await configureSettings(claudeDir, response.installType, mcpEnabled);
    
    // For project installs, also configure .mcp.json
    if (response.installType === 'project' && mcpEnabled) {
      await configureMCPProject(claudeDir, mcpEnabled);
    }

    spinner.succeed(chalk.green('Memory system installed successfully!'));

    // Print summary
    console.log('\n' + chalk.bold('📍 Installation Summary:'));
    console.log(`   Type: ${chalk.cyan(response.installType)}`);
    console.log(`   Location: ${chalk.cyan(claudeDir)}`);
    console.log(`   Commands: ${chalk.cyan('14 slash commands installed')}`);
    console.log(`   Hooks: ${chalk.cyan('3 automation hooks active')}`);
    if (mcpEnabled) {
      console.log(`   MCP Server: ${chalk.green('✓ Agent messaging enabled')}`);
    } else {
      console.log(`   MCP Server: ${chalk.yellow('⚠ Not configured (Python required)')}`);
    }
    
    console.log('\n' + chalk.bold('🚀 Next Steps:'));
    console.log('   1. ' + chalk.yellow('Restart Claude Code') + ' to activate hooks');
    console.log('   2. Test with: ' + chalk.yellow('/memory-status') + ' in Claude Code');
    console.log('   3. Or run: ' + chalk.yellow('claude-memory status') + ' in terminal');
    
    console.log('\n' + chalk.bold('📖 Quick Commands:'));
    console.log('   ' + chalk.gray('/memory-help') + ' - Show all commands');
    console.log('   ' + chalk.gray('/memory-search "term"') + ' - Search memories');
    console.log('   ' + chalk.gray('/memory-load agent "task"') + ' - Load context');
    
    if (mcpEnabled) {
      console.log('\n' + chalk.bold('💬 Agent Messaging:'));
      console.log('   Agents can now send messages to each other using MCP tools:');
      console.log('   ' + chalk.gray('create_message') + ' - Send message to another agent');
      console.log('   ' + chalk.gray('read_messages') + ' - Check messages from other agents');
    }
    
    console.log('\n' + chalk.bold('📚 Documentation:'));
    console.log(`   ${chalk.cyan(path.join(claudeDir, 'memory', 'README.md'))}`);
    
    console.log('\n' + chalk.green.bold('✨ Your subagents now have persistent memory!'));
    console.log(chalk.gray('\nThey will automatically remember lessons, share knowledge,'));
    console.log(chalk.gray('and build on past discoveries. No more repeated mistakes!\n'));

    // Check if Claude Code CLI is available
    try {
      execSync('which claude', { stdio: 'ignore' });
    } catch {
      console.log(chalk.yellow('\n⚠️  Note: Claude Code CLI not found in PATH'));
      console.log(chalk.gray('   Make sure the claude command is available for full functionality.\n'));
    }

  } catch (error) {
    spinner.fail(chalk.red('Installation failed'));
    console.error(chalk.red('\n✖ Error:'), error.message);
    console.log(chalk.gray('\nFor help, please visit:'));
    console.log(chalk.cyan('https://github.com/theo-nash/claude-memory-system/issues\n'));
    process.exit(1);
  }
}

// Handle uninstall command
if (process.argv.includes('--uninstall')) {
  (async () => {
    console.log(chalk.red('\n⚠️  This will remove the memory system'));
    
    const confirm = await prompts({
      type: 'confirm',
      name: 'value',
      message: 'Are you sure you want to uninstall?',
      initial: false
    });

    if (confirm.value) {
      // Remove from both locations
      const dirs = ['.claude/memory', '.claude/scripts/claude-memory', '.claude/scripts/memory-commands.sh'];
      const globalDirs = dirs.map(d => path.join(process.env.HOME, d));
      
      for (const dir of [...dirs, ...globalDirs]) {
        if (fs.existsSync(dir)) {
          fs.removeSync(dir);
        }
      }
      
      console.log(chalk.green('✓ Memory system uninstalled'));
    }
  })();
} else {
  // Run the installer
  main().catch(console.error);
}