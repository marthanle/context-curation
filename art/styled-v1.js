// Art Brief: a slow morning matcha ritual
// Canvas: 800 x 1000, p5.js global mode

let seed;

function setup() {
  createCanvas(800, 1000);
  seed = random(10000);
  noLoop(); // static / slow morning feel, redraws on interaction
}

function draw() {
  randomSeed(seed);
  
  // Warm cream background
  background(245, 240, 230);
  
  // Subtle grain / paper texture simulation
  drawTexture();
  
  // Calculate gentle mouse offsets for interactivity
  let mX = (mouseX - width / 2) * 0.03;
  let mY = (mouseY - height / 2) * 0.03;

  // Composition: Lots of empty space, off-center focal point
  // Soft organic form (steam / mist background shape)
  noStroke();
  fill(232, 199, 193, 70); // Soft blush
  ellipse(width / 2 + 50 + mX, height / 2 - 100 + mY, 400, 450);

  // Deep tea green circle (the bowl / focal point)
  fill(88, 129, 87); // Deep tea green
  let bowlX = width / 2 - 40 + mX * 0.5;
  let bowlY = height / 2 + 50 + mY * 0.5;
  
  // Hand-drawn feel organic circle
  push();
  translate(bowlX, bowlY);
  beginShape();
  for (let a = 0; a < TWO_PI; a += 0.1) {
    let r = 160 + random(-4, 4);
    let x = cos(a) * r;
    let y = sin(a) * (r * 0.7); // slightly oval
    vertex(x, y);
  }
  endShape(CLOSE);
  pop();

  // Matcha green inner tea liquid
  fill(163, 177, 138); // Matcha green
  push();
  translate(bowlX, bowlY - 10);
  beginShape();
  for (let a = 0; a < TWO_PI; a += 0.1) {
    let r = 130 + random(-3, 3);
    let x = cos(a) * r;
    let y = sin(a) * (r * 0.68);
    vertex(x, y);
  }
  endShape(CLOSE);
  pop();

  // Thin delicate lines (steam / ritual lines)
  stroke(58, 89, 87, 100);
  strokeWeight(1.5);
  noFill();
  
  beginShape();
  let startX = bowlX;
  let startY = bowlY - 80;
  vertex(startX, startY);
  bezierVertex(
    startX + 20 + mX, startY - 100, 
    startX - 30 + mX, startY - 200, 
    startX + 10 + mX, startY - 280
  );
  endShape();

  beginShape();
  let startX2 = bowlX - 30;
  let startY2 = bowlY - 70;
  vertex(startX2, startY2);
  bezierVertex(
    startX2 - 20 + mX, startY2 - 90, 
    startX2 + 30 + mX, startY2 - 180, 
    startX2 - 10 + mX, startY2 - 250
  );
  endShape();

  // Typography: small serif type, lowercase, generous spacing, tucked in a corner
  noStroke();
  fill(58, 58, 58); // Ink
  textFont('Georgia');
  textSize(13);
  // Simulating generous letter spacing via layout or standard text if spacing isn't native
  let title = "a slow morning matcha ritual";
  text(title, 100, height - 120);
  
  // Tiny refined caption
  textSize(10);
  fill(58, 58, 58, 150);
  text("plate i.", 100, height - 100);
}

// Moving the mouse gently changes the composition
function mouseMoved() {
  redraw();
}

// Clicking regenerates a new variation
function mousePressed() {
  seed = random(10000);
  redraw();
}

// Pressing S saves the canvas as a PNG
function keyPressed() {
  if (key === 's' || key === 'S') {
    saveCanvas('matcha-ritual', 'png');
  }
}

// Subtle risograph-like texture dots
function drawTexture() {
  noStroke();
  fill(58, 58, 58, 15);
  for (let i = 0; i < 1500; i++) {
    let x = random(width);
    let y = random(height);
    ellipse(x, y, 1.2, 1.2);
  }
}
