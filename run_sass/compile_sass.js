// Wrapper to compile `.sass` file safely

import * as sass  from 'sass';
import { readFileSync } from 'fs';

const USAGE = "run_sass.js <sass_file>";

function main() {
  const argv = process.argv ;
  if (argv.length <3) {
    // console.log(USAGE);
    process.exit(-1);
    //return;
  }
  const target = argv[2];
  const result = sass.compile(target);
  console.log(result.css);
}

main();
