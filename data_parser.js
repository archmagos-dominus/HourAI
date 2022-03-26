//encode data from the history of conversation (./datasets/livedata.json) to the main >
//> trainig dataset (./datasets/dataset.csv)

//import fs module to read/write from files
const fs = require('fs');
//import conversation data json
const cvs = require('./datasets/livedata.json');

//iterate thought the conversation data
for (let i in cvs) {
  //create first dialogue
  //format: `[NAME],"dialogue line"`
  line1 = cvs[i].username + ',' + '"' + cvs[i].userquote + '"';
  //append created line to dataset
  fs.appendFileSync('./datasets/dataset.csv', `\n${line1}`, 'utf-8');
  //create bot reply
  //format: `Hourai,"dialogue line"`
  line2 = 'Hourai' + ',' + '"' + cvs[i].botreply + '"';
  //append created line to dataset
  fs.appendFileSync('./datasets/dataset.csv', `\n${line2}`, 'utf-8');
}
