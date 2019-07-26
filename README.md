# gr-opssat

Author: Fischer Benjamin (benjamin.fischer@esa.int)

This repository contains documentation, and applications for receiving, demodulating, and decoding the UHF signal transmitted by the ESA OPS-SAT mission.

https://opssat1.esoc.esa.int/

https://www.esa.int/Our_Activities/Operations/OPS-SAT

### UHF specifications
Can be found in docs/os-uhf-specs.pdf

### Applications
1. UHF receiver application (os_uhf_rx.grc)
    1. Offset sampling (removal of the DC peak of SDRs)
    2. Doppler compensation (with GPredict)
    3. Frequency shifting to baseband and downsampling
    5. Noise suppressor (Squelch)
    4. ZMQ sink
2. OPS-SAT demodulator and decoder (os-demod-decode.grc)
    1. ZMQ source
    2. GMSK demodulator
    3. Decoder
    5. Output: Payload frame
    
### Dependencies
1. UHF receiver application (os_uhf_rx.grc)
    1. https://github.com/wnagele/gr-gpredict-doppler
2. OPS-SAT demodulator and decoder (os-demod-decode.grc)
    1. https://github.com/daniestevez/gr-satellites
    
### Recordings
A clean recording of the NanoCom AX100 beacon can be found in recordings/
