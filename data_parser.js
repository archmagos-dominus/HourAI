//encode data from the history of conversation (./convos.json) to the main >
//> trainig dataset (./lines.csv)

//import fs module to read/write from files
const fs = require('fs');
//import conversation data json
var cvs = require('./datasets/livedata.json');
//import dataset file
//var dataset = require('./datasets/dataset.csv')
//this is what you get for not making livedata an array mlem
var line_counter = 0;

//iterate thought the conversation data
for (let i in cvs) {
  //create first dialogue
  //format: `NAME,"dialogue line"`
  line1 = cvs[i].username + ',' + '"' + cvs[i].userquote + '"';
  //append created line to dataset
  fs.appendFileSync('./datasets/dataset.csv', `\n${line1}`, 'utf-8');
  //create bot reply
  //format: `Hourai,"dialogue line"`
  line2 = 'Hourai' + ',' + '"' + cvs[i].botreply + '"';
  //append created line to dataset
  fs.appendFileSync('./datasets/dataset.csv', `\n${line2}`, 'utf-8');
  line_counter++;
}

console.log(`Successfully parsed ${line_counter} messages to the main dataset.`)
