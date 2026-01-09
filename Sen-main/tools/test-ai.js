/**
 * AI Chat CLI Tool
 * Interactive chat với AI Assistant
 */
require("dotenv").config();
const readline = require("readline");
const aiService = require("../services/ai.service");

// Config
const USER_ID = 1; // Test user
const CONTEXT = {
  levelId: 1,
  characterId: 1,
  screenType: "DIALOGUE",
};

// Colors for terminal
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  cyan: "\x1b[36m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  red: "\x1b[31m",
  gray: "\x1b[90m",
  blue: "\x1b[34m",
};

// Create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: `${colors.cyan}You${colors.reset} > `,
});

console.log(
  `${colors.bright}${colors.blue}╔═══════════════════════════════════════════╗${colors.reset}`
);
console.log(
  `${colors.bright}${colors.blue}║     🤖 AI ASSISTANT CLI CHAT TOOL        ║${colors.reset}`
);
console.log(
  `${colors.bright}${colors.blue}╚═══════════════════════════════════════════╝${colors.reset}\n`
);

console.log(
  `${colors.gray}📌 API Key: ${aiService.API_KEY ? "✅ Configured" : "❌ Not set (using fallback)"
  }${colors.reset}`
);
console.log(`${colors.gray}📌 Model: ${aiService.MODEL}${colors.reset}`);
console.log(`${colors.gray}📌 User ID: ${USER_ID}${colors.reset}`);
console.log(
  `${colors.gray}📌 Context: Level ${CONTEXT.levelId}, Character ${CONTEXT.characterId}${colors.reset}\n`
);

console.log(`${colors.yellow}💡 Commands:${colors.reset}`);
console.log(`   ${colors.green}/help${colors.reset}    - Show help`);
console.log(`   ${colors.green}/clear${colors.reset}   - Clear chat history`);
console.log(`   ${colors.green}/context${colors.reset} - Show current context`);
console.log(`   ${colors.green}/exit${colors.reset}    - Exit chat\n`);

console.log(
  `${colors.bright}Type your message and press Enter to chat!${colors.reset}\n`
);

rl.prompt();

rl.on("line", async (input) => {
  const message = input.trim();

  // Handle empty input
  if (!message) {
    rl.prompt();
    return;
  }

  // Handle commands
  if (message.startsWith("/")) {
    handleCommand(message);
    rl.prompt();
    return;
  }

  // Chat with AI
  try {
    console.log(`${colors.gray}⏳ Thinking...${colors.reset}`);

    const startTime = Date.now();
    const result = await aiService.chat(USER_ID, message, CONTEXT);
    const duration = Date.now() - startTime;

    if (result.success) {
      console.log(
        `\n${colors.green}${colors.bright}AI${colors.reset} > ${result.data.message}`
      );
      console.log(`${colors.gray}   ⏱️  ${duration}ms${colors.reset}\n`);
    } else {
      console.log(`${colors.red}❌ Error: ${result.message}${colors.reset}\n`);
    }
  } catch (error) {
    console.log(`${colors.red}❌ Exception: ${error.message}${colors.reset}\n`);
  }

  rl.prompt();
});

rl.on("close", () => {
  console.log(
    `\n${colors.yellow}👋 Goodbye! Thanks for chatting!${colors.reset}`
  );
  process.exit(0);
});

function handleCommand(cmd) {
  const command = cmd.toLowerCase();

  switch (command) {
    case "/help":
      console.log(`\n${colors.bright}Available Commands:${colors.reset}`);
      console.log(
        `  ${colors.green}/help${colors.reset}    - Show this help message`
      );
      console.log(
        `  ${colors.green}/clear${colors.reset}   - Clear chat history from database`
      );
      console.log(
        `  ${colors.green}/context${colors.reset} - Show current chat context`
      );
      console.log(
        `  ${colors.green}/exit${colors.reset}    - Exit the chat application\n`
      );
      break;

    case "/clear":
      clearHistory();
      break;

    case "/context":
      console.log(`\n${colors.bright}Current Context:${colors.reset}`);
      console.log(`  User ID: ${colors.cyan}${USER_ID}${colors.reset}`);
      console.log(
        `  Level ID: ${colors.cyan}${CONTEXT.levelId || "None"}${colors.reset}`
      );
      console.log(
        `  Character ID: ${colors.cyan}${CONTEXT.characterId || "None"}${colors.reset
        }`
      );
      console.log(
        `  Screen Type: ${colors.cyan}${CONTEXT.screenType || "None"}${colors.reset
        }\n`
      );
      break;

    case "/exit":
    case "/quit":
      rl.close();
      break;

    default:
      console.log(`${colors.red}Unknown command: ${cmd}${colors.reset}`);
      console.log(
        `Type ${colors.green}/help${colors.reset} for available commands\n`
      );
  }
}

async function clearHistory() {
  try {
    const result = await aiService.clearHistory(USER_ID);
    if (result.success) {
      console.log(`${colors.green}✅ Chat history cleared!${colors.reset}\n`);
    } else {
      console.log(`${colors.red}❌ Failed to clear history${colors.reset}\n`);
    }
  } catch (error) {
    console.log(`${colors.red}❌ Error: ${error.message}${colors.reset}\n`);
  }
}
