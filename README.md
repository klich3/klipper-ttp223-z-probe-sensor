# Klipper TTP223 Z-Probe sensor

Z-endstop inductive sensor with 0.99$ costs.
The only thing to do is to solder three-pin cable jacks.
Configuration of TTP223 is by default A and B unsolded.

![ttp223-support](Images/sensor.png)

## SKR MINI v3.1

```
#BLTouch pinout

* PC14
* GND
* PA1 <- I/O
* PWR <- VCC
* GND <- GND
```

```
#Z-Stop pinout
* GND <- GND
* PC2 <- I/O
* Other 5v pin <- VCC
```

## printer.cfg

```
[probe]
pin: PA1 #(or PC2 if you use stock z-endstop pin)
x_offset: -43
y_offset: -13
speed: 2
lift_speed: 30.0
samples: 2
samples_result: median
sample_retract_dist: 2
samples_tolerance: 0.09
z_offset: 0.0 

[stepper_z]
endstop_pin: probe:z_virtual_endstop #^PC2
#position_endstop: 0.0 #removed because use bltouch
```

## Probe
1) run command `Z_PROBE`
2) after config offset run `SAVE_CONFIG`
3) accuracy `PROBE_ACCURACY`

### probe test results

```
probe accuracy results: maximum 0.042500, minimum -0.102500, range 0.145000, average -0.033250, median -0.043750, standard deviation 0.043345
probe at 125.000,125.000 is z=-0.102500
probe at 125.000,125.000 is z=-0.052500
probe at 125.000,125.000 is z=-0.077500
probe at 125.000,125.000 is z=-0.055000
probe at 125.000,125.000 is z=-0.037500
probe at 125.000,125.000 is z=-0.027500
probe at 125.000,125.000 is z=-0.005000
probe at 125.000,125.000 is z=-0.050000
probe at 125.000,125.000 is z=0.032500
probe at 125.000,125.000 is z=0.042500
PROBE_ACCURACY at X:125.000 Y:125.000 Z:10.000 (samples=10 retract=2.000 speed=2.0 lift_speed=30.0)
```

![ttp223-support](Images/cr10-ttp223-support1.png)
![ttp223-support](Images/cr10-ttp223-support2.png)
![ttp223-support](Images/cr10-ttp223-support3.png)
![ttp223-support](Images/IMG_4273.HEIC.jpg)

<video src="Images/IMG_4274.MOV-out.mp4" controls>

### Docs
   * https://github.com/bigtreetech/BIGTREETECH-SKR-mini-E3/blob/master/hardware/BTT%20SKR%20MINI%20E3%20V3.0/Hardware/BTT%20E3%20SKR%20MINI%20V3.0_PIN.pdf
   * https://infusionsystems.com/support/TTP223.pdf