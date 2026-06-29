const vm = require('vm');
const readline = require('readline');

// Persistent JavaScript execution context
const context = vm.createContext({
  console: {},
  process: process,
  Buffer: Buffer,
  setTimeout: setTimeout,
  clearTimeout: clearTimeout,
  require: require
});

let outputBuffer = [];

context.console.log = (...args) => {
  outputBuffer.push(args.map(a => typeof a === 'object' ? JSON.stringify(a) : a).join(' '));
};
context.console.error = (...args) => {
  outputBuffer.push('[ERROR] ' + args.map(a => typeof a === 'object' ? JSON.stringify(a) : a).join(' '));
};
context.console.info = context.console.log;
context.console.warn = context.console.warn;

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on('line', (line) => {
  try {
    const data = JSON.parse(line);
    const code = data.code || '';

    outputBuffer = [];

    // Run code inside persistent VM context
    const result = vm.runInContext(code, context);

    let resultStr = '';
    if (result !== undefined) {
      resultStr = typeof result === 'object' ? JSON.stringify(result) : String(result);
    }

    const response = {
      success: true,
      output: outputBuffer.join('\n') + (resultStr && outputBuffer.length ? '\n' : '') + resultStr,
      error: ''
    };
    process.stdout.write(JSON.stringify(response) + '\n');
  } catch (err) {
    const response = {
      success: false,
      output: outputBuffer.join('\n'),
      error: err.stack || err.message
    };
    process.stdout.write(JSON.stringify(response) + '\n');
  }
});
