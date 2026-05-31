DreamFinder — Image Upload Guide
==================================

Place your image files in the folders below. Mattress files are matched by the
mattress NAME (lowercased); accessory files by the Image File Name you enter in
the workbook. Send any common image format - everything is converted to JPG.

FOLDER STRUCTURE
----------------
  logos/
      store-logo.png        Your store logo (transparent background, min 400px wide)
      store-icon-192.png    Square PWA app icon, exactly 192 x 192 px
      store-icon-512.png    Square PWA app icon, exactly 512 x 512 px
      [brand]-logo.png      One logo per brand you carry (e.g. serta-logo.png)
                            These appear in the "Our Brands" footer section

  mattresses/
      <name>.(jpg|png|webp) One file per mattress, named to match the mattress
                            NAME (lowercased). Example: athena.jpg, royal-cloud.jpg

  accessories/
      <file>.(jpg|png|webp) One file per accessory, named to match that accessory's
                            Image File Name. Example: base-bt3000.jpg, copper-ice-regular.jpg

IMAGE SPECIFICATIONS
--------------------
  Mattresses:   Up to 1000px on the long edge   |  Any format (JPG/PNG/WebP) - converted to JPG
  Accessories:  Up to 1000px on the long edge   |  Any format (JPG/PNG/WebP) - converted to JPG
  Store Logo:   Min 400px wide                  |  PNG with transparent background (kept as-is)
  PWA Icons:    Exactly 192x192 / 512x512       |  PNG, square, no transparency (kept as-is)

ABOUT AUTO-CONVERSION
---------------------
  Mattress and accessory images are automatically resized to 1000px max
  and re-encoded as optimized JPG (quality 88) during build. So:

    - Send us the highest-quality source you have
    - DON'T pre-shrink, pre-compress, or pre-convert
    - DON'T worry about file size or format (JPG/PNG/WebP all fine as input)

  Logos and PWA icons are NOT auto-converted - those need to be PNG
  exactly as specified above.

NAMING RULES
------------
  - Use lowercase letters, numbers, and hyphens only
  - No spaces - use hyphens instead (e.g., "royal-cloud.jpg" not "Royal Cloud.jpg")
  - Mattress files: name to match the mattress NAME (lowercased), e.g. "Athena" -> athena.jpg
  - Accessory files: name to match the Image File Name in your workbook
  - Input extensions: .jpg, .jpeg, .png, or .webp (output is always JPG)

TIPS
----
  - Product images on a white or transparent background photograph best
  - If you don't have product shots, ask your manufacturer — they often have press images
