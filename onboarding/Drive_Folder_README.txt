DreamFinder — Image Upload Guide
==================================

Place your image files in the folders below. File names MUST match the
ID column in your spreadsheet exactly (including extension).

FOLDER STRUCTURE
----------------
  logos/
      store-logo.png        Your store logo (transparent background, min 400px wide)
      store-icon-192.png    Square PWA app icon, exactly 192 x 192 px
      store-icon-512.png    Square PWA app icon, exactly 512 x 512 px
      [brand]-logo.png      One logo per brand you carry (e.g. serta-logo.png)
                            These appear in the "Our Brands" footer section

  mattresses/
      [id].(webp|jpg|png)   One file per mattress, named to match the ID column
                            Example: athena.webp, royal-cloud.jpg

  accessories/
      [id].(webp|jpg|png)   One file per accessory, named to match the ID column
                            Example: base-bt3000.jpg, pillow-activecool.webp

IMAGE SPECIFICATIONS
--------------------
  Mattresses:   Up to 1000px on the long edge   |  WebP / JPG / PNG (auto-converted)
  Accessories:  Up to 1000px on the long edge   |  WebP / JPG / PNG (auto-converted)
  Store Logo:   Min 400px wide                  |  PNG with transparent background (kept as-is)
  PWA Icons:    Exactly 192x192 / 512x512       |  PNG, square, no transparency (kept as-is)

ABOUT AUTO-CONVERSION
---------------------
  Mattress and accessory images are automatically resized to 1000px max
  and re-encoded as WebP at quality 82 during build. The result is roughly
  100x smaller than the original with no visible loss. So:

    - Send us the highest-quality source you have
    - DON'T pre-shrink, pre-compress, or pre-convert
    - DON'T worry about file size

  Logos and PWA icons are NOT auto-converted — those need to be PNG
  exactly as specified above.

NAMING RULES
------------
  - Use lowercase letters, numbers, and hyphens only
  - No spaces — use hyphens instead (e.g., "royal-cloud.png" not "Royal Cloud.png")
  - The file name (without extension) must match the ID in your spreadsheet
  - Extensions: .png, .jpg, .jpeg, or .webp

TIPS
----
  - Product images on a white or transparent background photograph best
  - If you don't have product shots, ask your manufacturer — they often have press images
