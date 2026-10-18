'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),crypto=require('node:crypto'),path=require('node:path');
const ROOT=path.resolve(__dirname,'../..');
const config=JSON.parse(fs.readFileSync(path.join(ROOT,'league_config.yaml'),'utf8'));
const {defenseModifier,captainFactor}=require('./league-rules');
const players=v=>[{role:'P',pure_vote:v},...Array.from({length:4},()=>({role:'D',pure_vote:v}))];
test('all six screenshot bytes match source hashes',()=>{
 for(const s of Object.values(config.sources))assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT,s.path))).digest('hex'),s.sha256);
});
for(const [v,b] of [['5.99','0'],['6','0'],['6.249999','0'],['6.25','0.5'],['6.499999','0.5'],['6.5','1'],['6.749999','1'],['6.75','1.5'],['6.999999','1.5'],['7','2'],['8','2']])
 test('defense exact boundary '+v,()=>assert.equal(defenseModifier(players(v),config),b));
test('best three defenders plus keeper, not best four defenders',()=>{
 const p=players('7');p[0].pure_vote='5';p[4].pure_vote='10';
 assert.equal(defenseModifier(p,config),'2');
 p[4].pure_vote='7';assert.equal(defenseModifier(p,config),'1');
});
test('effective three-defender formation loses modifier',()=>assert.equal(defenseModifier(players('7').slice(0,4),config),'0'));
test('four effective defenders but one without valid vote loses modifier',()=>{
 const p=players('7');p[1].pure_vote=null;assert.equal(defenseModifier(p,config),'0');
});
test('political six is an eligible pure six',()=>{
 const p=players('6.5');p[1]={role:'D',kind:'POLITICAL_SIX',pure_vote:null};
 assert.equal(defenseModifier(p,config),'1');
});
test('office reserve is not eligible',()=>{
 const p=players('7');p[1].office_reserve=true;assert.equal(defenseModifier(p,config),'0');
});
test('SV yellow option is never silently enabled',()=>{
 const p=players('7');p[1]={role:'D',kind:'SV_YELLOW',pure_vote:null};
 assert.throws(()=>defenseModifier(p,config),/unknown/);
});
for(const [v,b] of [['4','-1.5'],['4.5','-1.5'],['5','-1'],['5.5','0'],['6','0'],['6.5','0'],['7','1'],['7.5','1.5'],['8','1.5']])
 test('captain observed band '+v,()=>assert.equal(captainFactor(v,'8',config),b));
test('vice applies only when captain without vote',()=>assert.equal(captainFactor(null,'7',config),'1'));
test('two SV remain unresolved',()=>assert.throws(()=>captainFactor(null,null,config),/not shown/));
test('unlisted decimal vote remains unresolved',()=>assert.throws(()=>captainFactor('5.25','7',config),/Unlisted/));
test('binary floating input is rejected',()=>assert.throws(()=>captainFactor(7,null,config),/string/));
test('no double bonus or malus and no office reserve',()=>{
 assert.equal(config.rules.captain_factor.double_bonuses,false);
 assert.equal(config.rules.captain_factor.double_penalties,false);
 assert.equal(config.rules.substitutions.office_reserve_enabled,false);
 assert.equal(config.rules.substitutions.maximum,5);
 assert.equal(config.release.gold_lock,false);
});
