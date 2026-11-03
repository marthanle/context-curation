// Art Brief: A slow morning matcha ritual
// Canvas: 800 x 1000, global mode p5.js
// Interactive: Mouse gentle change, Click regenerate, Press S saves PNG

let seed;
let palette;

function setup() {
  createCanvas(800, 1000);
  seed = floor(random(100000));
  
  // Palette from style-guide.md
  palette = {
    matcha: '#A3B18A',
    deepTea: '#588157',
    cream: '#F5F0E6',
    blush: '#E8C7C1',
    ink: '#3A3A3A'
  };
}

function draw() {
  randomSeed(seed);
  background(palette.cream);
  
  // Draw subtle paper/grain texture via quiet dots
  push();
  noStroke();
  fill(58, 89, 87, 8); // extremely subtle deep tea flecks
  for (let i = 0; i < 1200; i++) {
    let px = random(width);
    let py = random(height);
    ellipse(px, py, random(1, 2.5));
  }
  pop();

  // Mouse interaction offset (gentle change)
  let mX = (mouseX - width / 2) * 0.02;
  let mY = (mouseY - height / 2) * 0.02;

  // Editorial layout: lots of white space, off-center focal point
  let centerX = width * 0.48 + mX;
  let centerY = height * 0.52 + mY;

  // Soft organic background shape (Studio Ghibli soft light reference)
  push();
  noStroke();
  fill(palette.matchp || palette.matcha);
  // Using a soft translucent organic blob
  fill(163, 177, 138, 70);
  beginShape();
  for (let a = 0; a < TWO_PI; a += 0.2) {
    let xOff = map(cos(a), -1, 1, 0, 1.5);
    let yOff = map(sin(a), -1, 1, 0, 1.5);
    let r = 220 + noise(xOff, yOff, seed) * 40;
    let x = centerX + cos(a) * r;
    let y = centerY - 40 + sin(a) * (r * 0.7);
    vertex(x, y);
  }
  endShape(CLOSE);
  pop();

  // Steam rising softly (slow and quiet animation)
  push();
  noFill();
  stroke(palette.deepTea);
  strokeWeight(1.5);
  let time = millis() * 0.0008;
  for (let i = 0; i < 3; i++) {
    beginShape();
    let startX = centerX - 30 + i * 30;
    let startY = centerY - 140;
    for (let y = 0; y < 100; y += 5) {
      let wave = sin(time + y * 0.03 + i) * (y * 0.2);
      vertex(startX + wave, startY - y);
    }
    endShape();
  }
  pop();

  // Tea Bowl (recognized at a glance, side view, slightly from above)
  push();
  // Bowl body
  fill(palette.deepTea);
  noStroke();
  beginShape();
  let bowlW = 180;
  let bowlH = 100;
  // Hand-drawn wobbly edge approximation
  vertex(centerX - bowlW/2, centerY - 20);
  bezierVertex(
    centerX - bowlW/2 - 10, centerY + bowlH, 
    centerX + bowlW/2 + 10, centerY + bowlH, 
    centerX + bowlW/2, centerY - 20
  );
  endShape(CLOSE);

  // Rim / Inner ellipse showing matcha
  fill(palette.matcha);
  ellipse(centerX, centerY - 20, bowlW, 40);

  // Soft blush accent element (Editorial balance)
  noFill();
  stroke(palette.blush);
  strokeWeight(2);
  arc(centerX - 40, centerY + 180, 120, 60, PI, TWO_PI);
  pop();

  // Tiny refined caption / title (Georgia serif, lowercase, generous spacing)
  push();
  fill(palette.ink);
  noStroke();
  textFont('Georgia');
  textSize(13);
  // Simulating letter spacing by drawing characters or relying on minimal clean text
  // Since p5 doesn't have native letter-spacing easily without DOM, we keep it clean.
  text('a slow morning matcha ritual', 80, height - 90);
  pop();
}

function mousePressed() {
  seed = floor(random(100000));
}

function keyPressed() {
  if (key === 's' || key === 'S') {
    saveCanvas('matcha-ritual', 'png');
  }
}
