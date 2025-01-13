brlist
======

This is a tool to list linux bridges with their member interfaces.
As there is no good replacement for `brctl` in the iproute2 aera,
this tool aims to provide a similar user-friendly output.

```
 name | type   | bridge id              | bridge MAC        | STP | interfaces
------+--------+------------------------+-------------------+-----+------------
 br0  | bridge | 8000.a1:b2:c3:d4:e5:f6 | a1:b2:c3:d4:e5:f6 | no  | eth0
 br1  | ovs    | 8000.26:90:93:19:73:46 | 26:90:93:19:73:46 | yes | tap1
      |        |                        |                   |     | tap2
      |        |                        |                   |     | tap3
      |        |                        |                   |     | tap4
      |        |                        |                   |     | tap5
      |        |                        |                   |     | tap6
      |        |                        |                   |     | tap7
      |        |                        |                   |     | tap8
      |        |                        |                   |     | tap9
 br2  | bridge | 8000.62:96:9a:b6:94:30 | 62:96:9a:b6:94:30 | no  |
```


Filtering for bridge devices
----------------------------

By calling `brlist` with an arbitrary number of arguments each being
the name of a bridge, the output will be filtered to contain only
those bridges.

```
brlist br0 br2
```

When being called without any arguments `brlist` will show all bridges.
