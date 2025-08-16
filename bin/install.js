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

async function configureSettings(claudeDir, installType) {
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
      hook.command && hook.command.includes('add_trd_protocol.py')
    )
  );
  
  if (!sessionStartExists) {
    settings.hooks.SessionStart.push({
      hooks: [{
        type: 'command',
        command: `${hookPrefix}/add_trd_protocol.py`
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
  
  // Save updated settings
  await fs.writeJson(settingsPath, settings, { spaces: 2 });
}

async function main() {
  console.log(chalk.cyan(BANNER));
  console.log('This installer will set up persistent memory for your Claude Code subagents.\n');

  // Check if .claude exists
  const hasProjectClaude = fs.existsSync('.claude');
  const hasGlobalClaude = fs.existsSync(path.join(process.env.HOME, '.claude'));

  // Prompt for installation type
  const response = await prompts({
    type: 'select',
    name: 'installType',
    message: 'Where would you like to install the memory system?',
    choices: [
      { 
        title: 'Project (.claude)', 
        value: 'project', 
        description: 'Install in current project (recommended)' 
      },
      { 
        title: 'Global (~/.claude)', 
        value: 'global', 
        description: 'Install globally for all projects' 
      }
    ],
    initial: hasProjectClaude ? 0 : (hasGlobalClaude ? 1 : 0)
  });

  if (!response.installType) {
    console.log(chalk.red('\n✖ Installation cancelled'));
    process.exit(1);
  }

  const claudeDir = response.installType === 'global' 
    ? path.join(process.env.HOME, '.claude')
    : '.claude';

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
      'hooks/add_trd_protocol.py',
      'hooks/subagent_memory_analyzer.py',
      'hooks/context_cache_checker.py'
    ];

    for (const file of executableFiles) {
      const filePath = path.join(claudeDir, file);
      if (fs.existsSync(filePath)) {
        fs.chmodSync(filePath, '755');
      }
    }

    // Step 5: Configure settings.json with hooks and permissions
    spinner.text = 'Configuring hooks and permissions...';
    await configureSettings(claudeDir, response.installType);

    spinner.succeed(chalk.green('Memory system installed successfully!'));

    // Print summary
    console.log('\n' + chalk.bold('📍 Installation Summary:'));
    console.log(`   Type: ${chalk.cyan(response.installType)}`);
    console.log(`   Location: ${chalk.cyan(claudeDir)}`);
    console.log(`   Commands: ${chalk.cyan('14 slash commands installed')}`);
    console.log(`   Hooks: ${chalk.cyan('3 automation hooks active')}`);
    
    console.log('\n' + chalk.bold('🚀 Next Steps:'));
    console.log('   1. ' + chalk.yellow('Restart Claude Code') + ' to activate hooks');
    console.log('   2. Test with: ' + chalk.yellow('/memory-status') + ' in Claude Code');
    console.log('   3. Or run: ' + chalk.yellow('claude-memory status') + ' in terminal');
    
    console.log('\n' + chalk.bold('📖 Quick Commands:'));
    console.log('   ' + chalk.gray('/memory-help') + ' - Show all commands');
    console.log('   ' + chalk.gray('/memory-search "term"') + ' - Search memories');
    console.log('   ' + chalk.gray('/memory-load agent "task"') + ' - Load context');
    
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
    console.log(chalk.cyan('https://github.com/yourusername/claude-subagent-memory/issues\n'));
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