# Animation artwork

The shipped `assets/booboo-motion*.png` and `assets/moo-krata-motion*.png`
atlases each contain 25 frames in a 5×5 grid. The first 20 BooBoo drawings and
first 8 Moo Krata drawings come from the owner's `Desktop/pets/Booboo` and
`Desktop/pets/Moo Krata` folders. The remaining 5 and 17 drawings were
generated from those drawings as character references. The generated source
sheets are retained in `assets/generated/` so they can be reprocessed.

The generated prompts asked for the same white Holland lop grooming, yawning,
sniffing, alert and loafing; and the same tricolor fluffy puppy standing,
tilting, sniffing, sitting, resting, stretching, bowing, trotting, hopping and
landing. All assets have transparent backgrounds and no text or props.

To rebuild the atlases on a machine with the owner's original folders:

```sh
python -m pip install Pillow opencv-python
python scripts/build_pet_atlases.py --booboo "/path/to/pets/Booboo" --moo "/path/to/pets/Moo Krata"
```

Only the app's build process needs the PNG atlases; Pillow and OpenCV are not
runtime dependencies. Mac uses the smooth-alpha atlases; Windows uses the
binary-alpha versions to avoid a magenta fringe around the characters.
