// Theme: a slow morning matcha ritual
// Canvas: 800 x 1000, p5.js global mode

let seed;

function setup() {
  createCanvas(800, 1000);
  seed = floor(random(100000));
}

function draw() {
  randomSeed(seed);
  background(245, 243, 238); // Soft warm paper white

  let mX = mouseX;
  let mY = mouseY;

  // Subtle background organic gradients / rings representing steam or ripples
  noFill();
  strokeWeight(1.5);
  let numRings = 7;
  let centerX = width / 2 + map(mX, 0, width, -20, 20);
  let centerY = height / 2 + map(mY, 0, height, -20, 20);

  for (let i = 0; i < numRings; i++) {
    let radius = 100 + i * 50 + sin(frameCount * 0.02 + i) * 5;
    stroke(180, 195, 175, 40 + i * 15);
    beginShape();
    for (let a = 0; a < TWO_PI; a += 0.1) {
      let xOffset = map(noise(i, a, frameCount * 0.01), 0, 1, -10, 10);
      let yOffset = map(noise(i + 10, a, frameCount * 0.01), 0, 1, -10, 10);
      let x = centerX + cos(a) * (radius + xOffset);
      let y = centerY + sin(a) * (radius + yOffset);
      vertex(x, y);
    }
    endShape(CLOSE);
  }

  // The Matcha Bowl (Chawan) silhouette
  push();
  translate(centerX, centerY + 80);
  
  // Bowl shadow
  noStroke();
  fill(210, 205, 195, 100);
  ellipse(0, 140, 320, 40);

  // Bowl body
  fill(70, 60, 50); // Dark ceramic
  beginShape();
  vertex(-140, 0);
  bezierVertex(-150, 120, -100, 160, 0, 160);
  bezierVertex(100, 160, 150, 120, 140, 0);
  endShape(CLOSE);

  // Inner bowl / Matcha liquid
  fill(110, 140, 95); // Vibrant matcha green
  beginShape();
  vertex(-130, 10);
  bezierVertex(-135, 70, -80, 110, 0, 110);
  bezierVertex(80, 110, 135, 70, 130, 10);
  endShape(CLOSE);

  // Matcha surface foam / swirls
  noFill();
  stroke(140, 170, 120, 150);
  strokeWeight(3);
  for (let j = 0; j < 5; j++) {
    beginShape();
    let startX = random(-60, 60);
    let startY = random(20, 60);
    for (let t = 0; t < 50; t += 5) {
      let px = startX + t + sin(t + frameCount * 0.05 + j) * 10;
      let py = startY + cos(t * 0.1) * 5;
      vertex(px, py);
    }
    endShape();
  }

  pop();

  // Abstract morning sun / light arc
  noFill();
  stroke(225, 210, 190, 100);
  strokeWeight(2);
  arc(centerX, centerY - 150, 400, 400, PI, TWO_PI);

  // Typography (Short title on the poster)
  noStroke();
  fill(90, 85, 75);
  textAlign(CENTER, CENTER);
  textSize(24);
  textStyle(NORMAL);
  // Using default sans-serif as no external fonts are allowed per brief.md
  text("a slow morning matcha ritual", width / 2, height - 100);

  textSize(12);
  fill(150, 145, 135);
  text("MOVE MOUSE TO SHIFT  •  CLICK TO REGENERATE  •  PRESS S TO SAVE", width / 2, height - 60);
}

function mousePressed() {
  seed = floor(random(100000));
}

function keyPressed() {
  if (key === 's' || key === 'S') {
    saveCanvas('matcha-ritual', 'png');
  }
}
