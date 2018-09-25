## Latency setter script

Simulates the latencies among regions and availability zones, just like Amazon EC2.

## Requirements

Linux machine with `tc` command and python-netifaces installed.

## Usage

To set the latencies accordingly you will need two CSV files.

The first one provides the latency between pairs of availability zones (clusters),
while the second associates the nodes IPs to the corresponding zones.

You can find an example of both files (`latencies.csv` and `ips.csv`) under `./doc/sample`

To set the latency, simply run:

    sudo latency-setter.py set <ip-csv> <latency-csv> <interface-name>

The command will check if the IP address associated with the given interface is in IP file. If so,
the latencies will be set according to the latencies file and the zone where the node IP belongs to.

To undo the configuration, run:

    sudo latency-setter.py unset <interface-name>


## Notes

- You must run the commands as `root`
- Don't forget to undo the changes after running your experiments
- If you want to set the latencies for all the nodes, you can run the command in a loop:
```
for i in `cut -d , -f 2 <ip-csv>; do
    ssh $i "sudo latency-setter set <ip-csv> <latency-csv> <interface-name>"
done

#you will get an error about the first line because it does not contain a valid IP

```

Have fun!
