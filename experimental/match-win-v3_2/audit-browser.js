'use strict';
// Uses the preinstalled local Playwright runtime; no package installs or external calls.
const {chromium}=require('playwright'),fs=require('node:fs'),http=require('node:http'),path=require('node:path'),assert=require('node:assert/strict');
async function main(){
 const root=__dirname,server=http.createServer((req,res)=>{
  const p=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!p.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
  try{const data=fs.readFileSync(p);res.setHeader('Content-Type',p.endsWith('.html')?'text/html':'application/json');res.end(data);}catch{res.writeHead(404);res.end();}
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 let browser;const results=[];
 try{
  try{browser=await chromium.launch({headless:true});}catch(e){
   fs.writeFileSync(path.join(root,'ui-audit.json'),JSON.stringify({status:'BLOCKED_BROWSER_UNAVAILABLE',reason:e.message.split('\n')[0],physical_iphone_safari:'PENDING',results:[]},null,2)+'\n');
   console.log('UI_BROWSER_EXECUTION_BLOCKED: installed browser executable unavailable');process.exitCode=2;return;
  }
  for(const viewport of [{width:320,height:568},{width:390,height:844},{width:1440,height:900}]){
   const page=await browser.newPage({viewport}),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(`http://127.0.0.1:${server.address().port}/index.html`);
   assert.match(await page.locator('#warning').textContent(),/BLOCCATO/);assert.equal(await page.locator('#metrics').textContent().then(s=>s.includes('%')),false);
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   const b=await page.locator('#demo').boundingBox();assert.ok(b.height>=44);
   await page.locator('#demo').click();await page.waitForFunction(()=>document.getElementById('warning').textContent.includes('TEST SINTETICO'));
   assert.match(await page.locator('#context').textContent(),/TEST/);assert.ok(await page.locator('#xi li').count()===11);
   await page.locator('#report').setInputFiles({name:'blocked.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({status:'BLOCKED',gold:false,errors:['rules missing']}))});
   await page.waitForFunction(()=>document.getElementById('errors').textContent.includes('rules missing'));
   assert.equal(await page.locator('#xi li').count(),0);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);
   results.push({viewport,status:'PASS',no_horizontal_overflow:true,default_probabilities_null:true,synthetic_label_visible:true,blocked_import_clears_forecast:true,js_errors:errors});await page.close();
  }
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
 fs.writeFileSync(path.join(root,'ui-audit.json'),JSON.stringify({status:'PASS_CHROMIUM_AUTOMATED_ONLY',physical_iphone_safari:'PENDING',results},null,2)+'\n');
 console.log('UI_CHROMIUM_3_VIEWPORTS_PASS; PHYSICAL_IPHONE_PENDING');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
