# Data-Annotation
This is a quick [web tool](https://smt-research.github.io/Data-Annotation/) to classify sensor data for use in AI training.

## Usage
Drag a file containing the samples you want to classify into the webpage and the data will appear on screen, then use the following keybinds to interact with the data:
- **H**: Mark as Pass
- **J**: Mark as Observe
- **K**: Mark as Fail
- **L**: Mark as Error/Checksum
- **M**: Toggle marked as Wet/Dry
- **Space**: Next sample
- **Ctrl**: Previous sample

Once you have annotated the samples you can use the download button in the bottom right to download the labels in json format.

## Sample Generation
To generate the file containing the samples, we can use the [`get_data.py`](https://github.com/SMT-Research/Analytics-AI/blob/main/src/data/get_data.py) script found in 
the [Analytics-AI repository](https://github.com/SMT-Research/Analytics-AI). 
Using this script will download valid samples for an entire project, you can use [`merge_data.py`](https://github.com/SMT-Research/Analytics-AI/blob/main/src/data/merge_data.py)
to combine the samples from multiple projects together.

## Sample File Format
If you don't want to generate the sample data yourself without the script mentioned above, you can implement the file structure yourself.

Each sample has the following structure and are stacked on top of eachother in a sample file:

| Size          | Name       | Description                                                                                                                                                            |
|---------------|------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `8 bytes`     | Hash ID    | The first 8 bytes of the sha1 hash of the following data. Can be any identifier unique to the sample,  this is what's used to corelate the annotations to each sample. |
| `4*4 bytes`   | Sensor IDs | The 4 sensor ids as unsigned 32bit integers (r1, r2, v1, v1).                                                                                                          |
| `240*8 bytes` | X Data     | The 240 doubles representing timestamps. Used as x values for the rest of the data.                                                                                    |
| `240*8 bytes` | R1 Data    | The 240 doubles representing the values of this sensor.                                                                                                                |
| `240*8 bytes` | R2 Data    | ...                                                                                                                                                                    |
| `240*8 bytes` | V1 Data    | ...                                                                                                                                                                    |
| `240*8 bytes` | V2 Data    | ...                                                                                                                                                                    |

See the [examples folder](https://github.com/SMT-Research/Data-Annotation/tree/main/examples) for reference.