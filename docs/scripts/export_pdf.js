const path = require("path");
const puppeteer = require("puppeteer");

(async () => {
  // Parse command-line arguments
  const args = process.argv.slice(2);
  let url, output_file_stem;
  if (args.length > 0 && !args[0].startsWith("http")) {
    let input_file = path.resolve(args[0]);
    url = "file://" + input_file;
    let dirname = path.dirname(input_file);
    let basename = path.basename(input_file, ".html");
    output_file_stem = path.join(dirname, basename);
  } else {
    if (args.length > 0) {
      url = args[0];
    } else {
      url = "http://localhost:8000/";
    }
    output_file_stem = "screenshot";
  }
  console.log("url:", url);
  console.log("output_file_stem:", output_file_stem);

  const browser = await puppeteer.launch({
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: "networkidle0" });
  await page.setViewport({ width: 1200, height: 0, deviceScaleFactor: 3 });
  await page.emulateMedia("screen");

  // Get the "viewport" of the page, as reported by the page.
  const dimensions = await page.evaluate(() => {
    return {
      width: document.documentElement.offsetWidth,
      height: document.documentElement.offsetHeight,
      deviceScaleFactor: window.devicePixelRatio,
    };
  });
  console.log("Dimensions:", dimensions);

  await page.pdf({
    path: output_file_stem + ".pdf",
    width: `${dimensions["width"]}px`,
    height: `${dimensions["height"]}px`,
    pageRanges: "1",
    displayHeaderFooter: false,
    margin: { top: "0px", bottom: "0px" },
  });

  let screenshot_args = {
    path: output_file_stem + ".png",
    fullPage: true,
  };
  if (dimensions["height"] < 600) {
    screenshot_args = {
      ...screenshot_args,
      fullPage: false,
      clip: {
        x: 0,
        y: 0,
        width: dimensions["width"],
        height: dimensions["height"],
      },
    };
  }
  await page.screenshot(screenshot_args);
  await browser.close();
})();
