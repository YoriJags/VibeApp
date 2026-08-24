const puppeteer = require('puppeteer');
const path = require('path');
const { pathToFileURL } = require('url');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  const src = pathToFileURL(path.resolve(__dirname, 'viibe-pocket.html')).href;
  await page.goto(src, { waitUntil: 'networkidle0' });
  // let webfonts settle before painting
  await new Promise(r => setTimeout(r, 1500));
  const out = process.argv[2] || path.resolve(__dirname, 'VIIBE_Pocket_Brief.pdf');
  await page.pdf({
    path: out,
    width: '5.8333in',   // 420pt, phone-shaped so it fills a screen without zooming
    height: '10.9722in', // 790pt
    printBackground: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 },
  });
  await browser.close();
  console.log('PDF written:', out);
})();
