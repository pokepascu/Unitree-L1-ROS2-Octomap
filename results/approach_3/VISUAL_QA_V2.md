# Approach 3 RViz visual QA — refined v2

This diagnostic operates on the actual RViz PNG evidence and does not replace it.

The v1 detector was intentionally superseded because its corner-derived background estimate confused static RViz viewport content with mapped geometry. v2 uses the modal RGB color, exact color-frequency statistics, chromatic masks and inter-image differences.

## HcMR_lab

### isometric

- image: `1600x900` px
- modal viewport RGB: `(255, 255, 255)` covering `81.97%`
- chromatic fraction: `18.577%`
- non-background geometry proxy: `8.954%`
- chromatic bbox coverage: `61.6% x 98.1%`
- chromatic components >=20 px: `68`
- dominant RGB colors:
  - `(255, 255, 255)`: `81.97%`
  - `(0, 0, 255)`: `18.03%`
  - `(0, 0, 0)`: `0.01%`
  - `(255, 0, 0)`: `0.00%`
  - `(255, 255, 0)`: `0.00%`

### top

- image: `1600x900` px
- modal viewport RGB: `(255, 255, 255)` covering `91.37%`
- chromatic fraction: `9.474%`
- non-background geometry proxy: `1.196%`
- chromatic bbox coverage: `71.2% x 98.1%`
- chromatic components >=20 px: `68`
- dominant RGB colors:
  - `(255, 255, 255)`: `91.37%`
  - `(0, 0, 255)`: `8.62%`
  - `(0, 0, 0)`: `0.01%`
  - `(255, 0, 0)`: `0.00%`
  - `(255, 255, 0)`: `0.00%`

#### Top-view chromatic proxy

```text
@













                                              :
                                              @+
                                 +@@@@@@@@@@. @@
                                .@@@@@@@@@@@@@@@
                               =*@@@@@@@@@@@@@@@@@
                                 @@@@@@@@@@@@@@@-@@@@
                                 @@@@@@@@@@@@@@#:-.@@@:
                                 :@@@@@@@@@@@@@@@@@@@@@@.
                                  @@@@@@@@@@@@@#@@@@@@@@@*
                                  @@@@@@@@@@@@@@@@@@@@@@ :
                                  @@@@@@@@@@@@@@@@@@@@::
                                  @@@@@@@@@@@@@@@@@@@%@@
                                  @@@@@@@@@@@@@@@@@@@@@@
                                  :@@@@@@@@@@@@@@@@@@@@
                                  +@@@@@@@@@@@@@@@@@@@:
                                  +@@@@@@@@@@@@@@@@@@@
                                   @@@@@@@@@@@@@@@@@@
                                   @@@@@@@@@@@@@@@@*
                                   @@@@@@@@@@@@@@@-
                                  -@@@@@@@@@@@@@@
                           =     @@@@@@@@@@@@@@@
                           @@   :@@@@@@@@@@@@@@
```

#### Top-view non-background proxy

```text
@=
%=













                                              #
                                          .   @
                                  --:  . ..-=*+:
                                 :+  .    ::...**
                                 .+.-=     .     .:::
                                  @ . .    :       .=-
                                  :.     : :.   .   .:@=
                                   ..      .    =.     :-
                                   +.    -. =. -=.= .
                                          ..#@@%=.:.:
                                         :.:**#+=::.. :.
                                     -  :--=#==-=**. -@:
                                   :.-=+-=%:+.:::@@++%.
                                   -+##==#--++=:.-.+@#
                                   #*@#-==+*+*=-#+@@*
                                   #%#%#-=+*+%@=-@@*-
                                   *+-+===+++=@@@@+
                                   =@=*=:-#*%@@@@*.
                                  :@%*=--:#*%%%@=
                                 =@@..::-=*=:+:*
:                          --    @@ .==:=-.  .@
```

### side

- image: `1600x900` px
- modal viewport RGB: `(255, 255, 255)` covering `87.94%`
- chromatic fraction: `12.193%`
- non-background geometry proxy: `11.778%`
- chromatic bbox coverage: `71.9% x 76.2%`
- chromatic components >=20 px: `18`
- dominant RGB colors:
  - `(255, 255, 255)`: `87.94%`
  - `(0, 0, 255)`: `12.06%`
  - `(0, 0, 0)`: `0.01%`
  - `(255, 0, 0)`: `0.00%`

## ISR_5th_floor_run_1

### isometric

- image: `1600x900` px
- modal viewport RGB: `(255, 255, 255)` covering `95.18%`
- chromatic fraction: `5.575%`
- non-background geometry proxy: `4.683%`
- chromatic bbox coverage: `58.2% x 62.5%`
- chromatic components >=20 px: `52`
- dominant RGB colors:
  - `(255, 255, 255)`: `95.18%`
  - `(0, 0, 255)`: `4.82%`
  - `(0, 0, 0)`: `0.01%`
  - `(255, 0, 0)`: `0.00%`

### top

- image: `1600x900` px
- modal viewport RGB: `(255, 255, 255)` covering `95.29%`
- chromatic fraction: `5.826%`
- non-background geometry proxy: `3.750%`
- chromatic bbox coverage: `56.8% x 81.0%`
- chromatic components >=20 px: `123`
- dominant RGB colors:
  - `(255, 255, 255)`: `95.29%`
  - `(0, 0, 255)`: `4.70%`
  - `(0, 0, 0)`: `0.01%`
  - `(255, 0, 0)`: `0.00%`

#### Top-view chromatic proxy

```text
@












                         . .: .:::.   =:#+
           ...   .- . ##@@@@@@@@@@@@*.#@@@@*
    *==@@@@@@=%. @@#  ==@@@@@@@@@@@@.: @@@@
   =@@@@@@@@@+   .@=   :@@@@@@@@@@@@*+-%@@-
   %@@@@@@@@@%-@@@@@#   @@@@@@@@@@@@@@@@@@.
   @@@@@@@@@@@ @@@@@@@@@@@@@@@@@@@@@@@@@@@@=
   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-
   @@@@@@@@@@@#  -@@@   @.--    . @@   @@@ : =
   @@@@*##@ @@@  :@@+  *@+        @@         @
   @@*      @@=   @*:  @@.        @*.        @
   @::     :@@%   --. .@@%        @@        :@
   @.=     -@@@   .+  +@@:       :@+        =@
   @-      -%@+   ...  @@.        @=.
   @-=.     ==+        #+         @
   -+      . ..
   -.






```

#### Top-view non-background proxy

```text
@=
%=











                                .     . :.
                      .:-+---=-=%-==  .*@@@:
    .. -. :::.:  ::.  . -+++++#*+===   @@@+
    =-* =:==:     :     +%+=-+**:=*-:..:@@
   .::+-#=+++: #@%@@-   @@@@%%#@@@@@@@@@@@
   ++++%@@@@@@ ==:-@@*%@@@@@@@@@@@@@@@@@@@%
   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-
   @@@@@@@@@@@@@@@@@@@##@@@@@@*@@@@%+==@@@=.
   @@@@@@@@@@@:  .@@-   @         #@   =@#
   @@+=:... *@-   @..  .@:        @*         .
   =@       #@.   -.   @@         @.         +
   *        *@:   ..   @@-        @=        .-
   . .      =%.    :  .#@         @.        .=
   -.       .=.        -@         *.
   .                   .          .
    .






:
```

### side

- image: `1600x900` px
- modal viewport RGB: `(255, 255, 255)` covering `97.93%`
- chromatic fraction: `2.344%`
- non-background geometry proxy: `2.093%`
- chromatic bbox coverage: `57.5% x 53.3%`
- chromatic components >=20 px: `15`
- dominant RGB colors:
  - `(255, 255, 255)`: `97.93%`
  - `(0, 0, 255)`: `2.06%`
  - `(0, 0, 0)`: `0.01%`
  - `(255, 0, 0)`: `0.00%`

## ISR_5th_floor_run_2

### isometric

- image: `1600x900` px
- modal viewport RGB: `(255, 255, 255)` covering `98.52%`
- chromatic fraction: `1.732%`
- non-background geometry proxy: `1.454%`
- chromatic bbox coverage: `48.8% x 18.5%`
- chromatic components >=20 px: `10`
- dominant RGB colors:
  - `(255, 255, 255)`: `98.52%`
  - `(0, 0, 255)`: `1.48%`
  - `(0, 0, 0)`: `0.01%`
  - `(255, 0, 0)`: `0.00%`

### top

- image: `1600x900` px
- modal viewport RGB: `(255, 255, 255)` covering `99.99%`
- chromatic fraction: `0.014%`
- non-background geometry proxy: `0.027%`
- chromatic bbox coverage: `6.8% x 5.8%`
- chromatic components >=20 px: `2`
- dominant RGB colors:
  - `(255, 255, 255)`: `99.99%`
  - `(0, 0, 0)`: `0.01%`
  - `(0, 0, 255)`: `0.00%`
  - `(255, 0, 0)`: `0.00%`

#### Top-view chromatic proxy

```text
@  :
   *:
   . .

































```

#### Top-view non-background proxy

```text
@=
%= .

































:
```

### side

- image: `1600x900` px
- modal viewport RGB: `(255, 255, 255)` covering `99.70%`
- chromatic fraction: `0.340%`
- non-background geometry proxy: `0.307%`
- chromatic bbox coverage: `19.6% x 48.1%`
- chromatic components >=20 px: `4`
- dominant RGB colors:
  - `(255, 255, 255)`: `99.70%`
  - `(0, 0, 255)`: `0.29%`
  - `(0, 0, 0)`: `0.01%`
  - `(255, 0, 0)`: `0.00%`

## Pairwise top-view image differences

Mean absolute RGB differences after the identical viewport crop:

- `HcMR_lab` vs `ISR_5th_floor_run_1`: `0.03430` normalized RGB MAD
- `HcMR_lab` vs `ISR_5th_floor_run_2`: `0.02536` normalized RGB MAD
- `ISR_5th_floor_run_1` vs `ISR_5th_floor_run_2`: `0.01427` normalized RGB MAD

## Interpretation guardrail

Very low chromatic content is flagged for manual investigation but is not automatically called an empty map, because OctoMap/RViz marker colors can be low-saturation depending on the display. The modal palette, non-background proxy and inter-image differences must be considered together.
