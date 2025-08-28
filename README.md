# Data-Annotation
This is a quick [web tool](https://smt-research.github.io/Data-Annotation/) to classify sensor data for use in AI training.

## Usage
Drag a file containing the samples you want to classify into the webpage and the data will appear on screen, then use the following keybinds to interact with the data;
- **H**: Mark as Pass
- **J**: Mark as Observe
- **K**: Mark as Fail
- **L**: Mark as Error/Checksum
- **M**: Toggle marked as Wet/Dry
- **Space**: Next sample
- **Ctrl**: Previous sample

Once you have annotated the samples you can use the download button in the bottom right to download the labels in json format.

## Sample Generation
To generate the file containing the samples, we can use a script found in the [Analytics-AI repository](https://github.com/SMT-Research/Analytics-AI/blob/main/src/data/get_data.py). 
Using this script will download valid samples for an entire project, you can use [`merge_data.py`](https://github.com/SMT-Research/Analytics-AI/blob/main/src/data/merge_data.py)
to combine the samples from multiple projects together.
