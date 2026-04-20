import Anthropic from "@anthropic-ai/sdk";
import * as dotenv from "dotenv";
import * as readline from "readline";

dotenv.config();

const client = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
});

const history = [];

async function chat(userMessage){
    history.push({
        role: "user",
        content: userMessage,
    });

    const response = await client.messages.create({
        model: "claude-sonnet-4-5",
        max_tokens: 1024,
        system: "You are a helpful assistasnt.",
        messages: history,
    });


    const assistantMessage = response.content[0].text;
    history.push({
        role: "assistant",
        content: assistantMessage,
    })

    return assistantMessage;
}

async function main() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
    })


    console.log("Claude JS Chatbot - type 'quit' to exit\n");

    const askQuestion = () => {
        rl.question("You: ", async (input) => {
            const userInput = input.trim();

            if (userInput.toLowerCase() === "quit"){
                console.log("Goodbye!");
                rl.close();
                return;
            }
            if (userInput){
                const response = await chat(userInput);
                console.log(`\nClauded: ${response}\n`);
            }

            askQuestion();
        });
    };
    askQuestion();
}

main();