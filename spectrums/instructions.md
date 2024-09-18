# What is here?

Folders with saved spectra for correlation with current VCSELL spectrum.
Name of a folder is approximate frequency where it could be used.

## Naming of files

`<index -10 to 10>_<value of out voltage>_<value of difference between Pump and Zero levels>.npy`

The index 0 is meant for a zero detuning, increments of 1 are given for steps of 10mV in output voltage

> **_NOTE:_**  This voltage is sent to trim input over 100K serial resistor that forms voltage divider with its internal impedance of 2k.