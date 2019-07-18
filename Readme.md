# KX3tools

Python scripts to interact with an [Elecraft](https://elecraft.com) KX3.

## swr.py

This script uses the KX3 to determine the SWR on a given set of frequencies with and without the internal KXA3 tuner. Here's an example output for an 58ft wire antenna:

| Freq(KHz) | SWR       | SWRt      | L         | C         | Side      |
|-----------|-----------|-----------|-----------|-----------|-----------|
| 1860      | 60.2      | 20.5      | 9.56      | 203.0     | TX        |
| 3690      | 14.2      | 1.2       | 2.43      | 1872.0    | ANT       |
| 7090      | 20.3      | 1.2       | 0.5       | 1790.0    | ANT       |
| 14285     | 9.9       | 1.2       | 1.37      | 203.0     | TX        |
| 21285     | 9.1       | 1.4       | 0.5       | 164.0     | ANT       |
