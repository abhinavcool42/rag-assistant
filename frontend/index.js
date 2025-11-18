const axios = require('axios');
const prompts = require('prompts');
const ora = require('ora');
const chalk = require('chalk');

// Ensure this URL matches your running Flask backend
const API_URL = 'http://127.0.0.1:5000/api/query';

async function main() {
    // Clear the terminal screen for a fresh start
    console.clear();
    console.log(chalk.cyan.bold('🤖 RAG AI Assistant CLI'));
    console.log(chalk.gray('Type "exit" to quit.\n'));

    while (true) {
        // 1. Get User Input
        const response = await prompts({
            type: 'text',
            name: 'query',
            message: chalk.yellow('You:'),
            validate: value => value.length > 0 ? true : 'Please enter a question.'
        });

        // Handle exit command
        if (!response.query || response.query.toLowerCase() === 'exit') {
            console.log(chalk.green('\nGoodbye! 👋'));
            break;
        }

        // 2. Show loading spinner while waiting for backend
        const spinner = ora('Thinking...').start();

        try {
            // 3. Send POST request to Python Backend
            const result = await axios.post(API_URL, {
                query: response.query
            });

            spinner.stop();

            // 4. Extract data from response
            const answer = result.data.answer;
            const sources = result.data.retrieved_context;

            // 5. Display Answer
            console.log('\n' + chalk.blue.bold('AI: ') + answer + '\n');

            // 6. Display Sources (if they exist)
            if (sources && sources.length > 0) {
                console.log(chalk.gray('--- Sources ---'));
                sources.forEach((src, i) => {
                    // Clean up newlines for better CLI display
                    const snippet = src.replace(/\n/g, ' ').substring(0, 100) + '...';
                    console.log(chalk.dim(`[${i + 1}] ${snippet}`));
                });
                console.log(chalk.gray('---------------\n'));
            }

        } catch (error) {
            spinner.fail('Error');
            if (error.code === 'ECONNREFUSED') {
                console.log(chalk.red('Could not connect to backend. Is "app.py" running on port 5000?'));
            } else {
                console.log(chalk.red(`Server Error: ${error.message}`));
            }
            console.log('\n');
        }
    }
}

main();