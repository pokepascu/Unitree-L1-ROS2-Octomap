# Approach 3 RViz visual QA — trajectory-fitted v3

This diagnostic is computed from the actual final RViz PNG captures after trajectory-centered camera fitting. It does not replace the screenshots and is not a metrological map-accuracy score.

The OctoMap MarkerArray is blue in these captures. The QA therefore measures blue occupied-cell visibility inside the cropped RViz viewport. A minimum 0.1% visible blue fraction is used as a conservative presentation diagnostic in every final view.

## HcMR_lab

- trajectory center XY: `[8.41657046723543, -1.50120753646422]` m
- trajectory span XY: `[16.83314093447086, 3.0769844205495738]` m
- fitted RViz distance: `39.031` m

### isometric

- blue OctoMap viewport fraction: `1.805%`
- blue bbox coverage XY: `55.1% x 54.1%`
- blue centroid normalized XY: `(0.409, 0.584)`
- blue components >=20 px: `136`
- visibility gate: `PASS`

### top

- blue OctoMap viewport fraction: `7.304%`
- blue bbox coverage XY: `33.3% x 77.8%`
- blue centroid normalized XY: `(0.538, 0.561)`
- blue components >=20 px: `732`
- visibility gate: `PASS`

#### Top-view blue occupancy proxy

```text





                                             :%
                                   @@@@@@@@@: @
                                 :@@@@@@@@@@@@@%=
                                 :-@@@@@@@@@@@@=@@@-
                                   @@@@@@@@@@@@::+@@#.
                                   @@@@@@@@@@@%#@@@@@@*
                                   @@@@@@@@@@@@@@@@@@@@
                                   :@@@@@@@@@@@@@@@@-.
                                    @@@@@@@@@@@@@@@%@@
                                    @@@@@@@@@@@@@@+@@*
                                    @@@@@@@@@@@@@@@@#
                                   .@@@@@@@@@@@@@@@#
                                    @@@@@@@@@@@@@@#
                                    @@@@@@@@@@@@@
                                    %@@@@@@@@@@@
                             :     %@@@@@@@@@@@.
                             .-   @@@@@@@@@@@@@
                             :@  @@@@@@@@@@@@@@
                             :@.@@@@@@@@@@@@@@@
                              @@@@@@@@@@@@@@@@@-
                              @@@@@@@@@@@@@@@@@@
                               @@@@@@@@@@@@@@@@@
                                 @@@@@@@@@@@@@@@
                                   #@@@@@@@@#.
                                       %


```

### side

- blue OctoMap viewport fraction: `0.000%`
- blue bbox coverage XY: `0.0% x 0.0%`
- blue centroid normalized XY: `(0.000, 0.000)`
- blue components >=20 px: `0`
- visibility gate: `FAIL`

## ISR_5th_floor_run_1

- trajectory center XY: `[20.217530136869456, -49.23082514184736]` m
- trajectory span XY: `[40.43506027373891, 98.99478890913863]` m
- fitted RViz distance: `152.214` m

### isometric

- blue OctoMap viewport fraction: `0.000%`
- blue bbox coverage XY: `0.0% x 0.0%`
- blue centroid normalized XY: `(0.000, 0.000)`
- blue components >=20 px: `0`
- visibility gate: `FAIL`

### top

- blue OctoMap viewport fraction: `0.004%`
- blue bbox coverage XY: `46.7% x 19.8%`
- blue centroid normalized XY: `(0.546, 0.404)`
- blue components >=20 px: `0`
- visibility gate: `FAIL`

#### Top-view blue occupancy proxy

```text











                                                .
                                          :. ..         .
                                 ..




                     .













```

### side

- blue OctoMap viewport fraction: `0.000%`
- blue bbox coverage XY: `0.0% x 0.0%`
- blue centroid normalized XY: `(0.000, 0.000)`
- blue components >=20 px: `0`
- visibility gate: `FAIL`

## ISR_5th_floor_run_2

- trajectory center XY: `[4.514650174717076, -76.81967923190754]` m
- trajectory span XY: `[77.01163854700104, 48.21429126854426]` m
- fitted RViz distance: `92.293` m

### isometric

- blue OctoMap viewport fraction: `0.016%`
- blue bbox coverage XY: `34.7% x 22.7%`
- blue centroid normalized XY: `(0.197, 0.633)`
- blue components >=20 px: `0`
- visibility gate: `FAIL`

### top

- blue OctoMap viewport fraction: `0.803%`
- blue bbox coverage XY: `47.1% x 97.7%`
- blue centroid normalized XY: `(0.461, 0.580)`
- blue components >=20 px: `97`
- visibility gate: `PASS`

#### Top-view blue occupancy proxy

```text
                                                    .+@
                                                     @@-
                                                   :-#
                                                 :-@*
                                                 @@@
                                               %=@*
                                               +:%
                                              -@=.
                                             -@@.
                                           .+@@
                                           -@+
                                        . @@@
                                      :+%@@-
                                      @@@@
                                  ...@@@@
                               .  .@=@@=
                                 =@@@@*
                             ..:@@@@*=..
                            ..@@@@@
                            .@@@@*
                            @@@%.
                          .@@@*
                          .@@#:
                          #@#
                         :@@.
                       .+@@*
                    +-==.@%.
                   .-*%@@=.
                    -#@@@%    .:
                      @*=+: -=%=*-.
                     ...@=#+= +@@+..
                          @%::@@@@@:.
```

### side

- blue OctoMap viewport fraction: `0.000%`
- blue bbox coverage XY: `0.0% x 0.0%`
- blue centroid normalized XY: `(0.000, 0.000)`
- blue components >=20 px: `0`
- visibility gate: `FAIL`

## Overall result

**FAIL**

Failed views: HcMR_lab/side, ISR_5th_floor_run_1/isometric, ISR_5th_floor_run_1/top, ISR_5th_floor_run_1/side, ISR_5th_floor_run_2/isometric, ISR_5th_floor_run_2/side

A PASS establishes that the trajectory-fitted captures contain a materially visible OctoMap in all three canonical views. It does not establish the absolute accuracy of the +23 deg mounting yaw, which remains a documented fixed-mount working constraint rather than an independently measured calibration.

If this report says FAIL, the report is intentionally still preserved and committed so the failing view can be corrected from quantitative evidence rather than guessed.
