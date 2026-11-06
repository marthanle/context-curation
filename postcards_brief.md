Build a public website called "postcards from places i love" that turns my trips into an interactive postcard series. Use everything in the context: my style guide, my dislikes, the trip itineraries, my notes for each stop, and the photo descriptions.

Photos: each photo in the context is labeled with a path like trips/france-2026/01-chamonix/R0002461.JPG. In the website, reference it by replacing "trips/" with "photos/", like photos/france-2026/01-chamonix/R0002461.JPG. Only use photos that appear in the context. Keep every photo in its natural, original colors. Do not tint, desaturate, or add color overlays or filters to any photo.

Page layout, top to bottom:
1. A tiny letterspaced label "a personal collection" in small serif.
2. A large italic serif title "postcards from places i love."
3. A row of lowercase trip tabs, one for each trip folder in the context (like "france 2026"). Only show trips that exist in the context. The active tab is underlined in deep tea green.
4. A thin divider line.
5. The postcard carousel (described below).
6. Below the carousel, a row of lowercase city tabs for the current trip, one per stop folder in order (like "chamonix", "annecy", "paris"). The active city is underlined in deep tea green. In the center of that row, small italic text: "click a postcard to turn it over".
7. A thin divider line and a tiny footer: "collected slowly, kept forever."

Carousel: the carousel only shows postcards for the selected city. Every photo from that city becomes its own postcard. One postcard sits large in the center, and the previous and next postcards peek out behind it on the left and right, smaller, slightly faded, and tilted a few degrees, like cards spread on a table. Thin arrow buttons on the far left and right move between postcards, with a smooth slide animation. Left and right arrow keys and swiping on phones also work. Clicking a city tab switches the carousel to that city's postcards and starts at the first one. Clicking a trip tab switches to that trip and its first city.

Postcard size: every postcard is a landscape rectangle with the proportions of a real 6 x 4 inch postcard. Use aspect-ratio: 3 / 2. The center postcard is min(80vw, 560px) wide. Front and back are exactly the same size.

Front of each postcard: the photo fills the card inside a thin cream border, cropped with object-fit: cover so it is never squished. Below the photo, on the cream border, a small lowercase serif caption with the place and country like "chamonix, france" on the left, and "plate i.", "plate ii.", and so on on the right, numbered within that city. Soft drop shadow under the card.

Back of each postcard: only the center postcard can flip. Clicking it flips it over with a smooth 3D animation, and clicking again flips it back. Design the back like a real vintage postcard, using this exact layout:
- The back face is a CSS grid with two columns: grid-template-columns: 58% 42%. Background around #FBF8F1 with very subtle paper grain, same thin border and soft shadow as the front, and about 28px of padding.
- Left column: the handwritten note in Caveat, dark ink gray, lowercase, about 22px, broken into 3 or 4 short lines. The left column uses display: flex with align-items: center and justify-content: center so the note sits in the vertical middle of the card, not at the top. The note text itself is left-aligned like real handwriting, never centered, with about 24px of left padding. Keep the note to 10 to 30 words. Each postcard gets its own note based on that specific photo and my notes for that stop. Write it the way I would actually text a friend: first person (I, we, me), casual, and specific, using real details from my notes. It should never sound like a photo caption or description. Good: 'we got soft serve in the snow and it was so worth it'. Bad: 'savoring delicious ice cream cones in a cozy casual setting'.
- The divider is a 1px sage green border-left on the right column, running the full height of the card. There is no other vertical line.
- Right column, top right corner: a soft blush pink stamp drawn with inline SVG, about 70px wide, with a scalloped perforated edge. Inside it, a simple thin-line illustration in deep tea green that matches the place, and the tiny letterspaced word "souvenir" at the bottom.
- A faded gray postmark drawn with inline SVG, about 80px: two thin solid concentric circles, with the place name in small caps curving along the top inside the outer ring using an SVG textPath on an arc (the text must follow the curve, never run straight up and down), and a few short wavy cancellation lines extending to the left of the circle. Position it absolutely so it overlaps the lower left corner of the stamp, rotated about -12 degrees, at about 60% opacity.
- Right column, below the stamp: three thin sage green address lines, evenly spaced in the lower half of the column. They stay completely inside the right column and never cross the divider.

Flip requirement: attach the click listener to the outer postcard container, not the front face, and toggle a "flipped" class on and off every click. Both faces use backface-visibility: hidden, and nothing on the back face (including the SVG stamp and postmark) can block clicks. Moving to another postcard or city resets any flipped card to its front.

Rules: follow my palette and dislikes for everything except the photos themselves. Warm cream background with very subtle paper grain. Use Google Fonts: a serif like Cormorant Garamond or Georgia for all text, and Caveat for the handwritten message. Lots of empty space. Must work on phones. Never include booking or confirmation numbers, addresses, phone numbers, prices, or anyone's last name. Do not use em dashes in any text.

Return one complete self-contained HTML file with all CSS and JavaScript inline and no frameworks, inside a single html code block.

Photo filenames: copy every photo filename exactly as it appears in the context, character for character, including uppercase or lowercase file extensions (.JPG vs .jpg). Never invent or guess a filename.

Single-city trips: if a trip has only one stop folder, still show its single city tab below the carousel so every trip has the same layout.

Trip tab order (required): store all trips in one JavaScript array of objects, each with a "name" like "banff" and a "year" like 2025. Before rendering any tabs, sort that array in JavaScript with exactly this code:
trips.sort((a, b) => a.year - b.year || a.name.localeCompare(b.name));
Then build the trip tabs from the sorted array, and select the first trip in the sorted array when the page loads. Do not hardcode tab order in the HTML.

Photo paths (required): the src for every image must start with "photos/" followed directly by the trip folder, like photos/banff-2025/01-banff/R0000420.jpg. Never include "trips/" anywhere in an image path.

Japan captions: for the japan-2026 trip, every postcard caption is just "japan" and the city tab is just "japan". Do not name a specific city like Sapporo or Tokyo in the caption, stamp, or postmark. In the handwritten messages, only name a city if the photo description clearly shows a famous landmark from that city. Otherwise keep the message about the moment, not the location.


Japan stamp: the stamp illustration for the japan-2026 trip is a simple thin-line Mt. Fuji with a small sun.
