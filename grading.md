## Hößl (13/15P)

### 1 Karaoke Game (6/6P)

 * frequency detection
   * works great (+3)
 * game
   * indistinguishable from SingStar (+2)
 * latency
   * super snappy (+1)

### 2 Whistle Input (6/8P)

 * whiste detection
   * had to do a bit of fiddling around - seems like THRESHOLD was way too low for my microphone settings. Calibration would have been nice. (-1)
   * no confusion between up and down whistling (good!) and it worked ok once everything was calibrated (+2)
 * robust against noise
   * was able to trigger events by clapping and hissing (-1)
   * did not trigger from ordinary background noise (+1)
 * latency
   * fine (+1)
 * pyglet test program
   * works, but a longer list would have been nice. (+1)
 * triggered key events
   * works (+1)

## Bonus Point: (1/1P)

Looks good overall, but a bit clearer variable names (e.g. AMPLITUDE_THRESHOLD instead of THRESHOLD) would have helped debugging. (+1)
