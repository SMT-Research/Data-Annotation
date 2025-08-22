const INPUT_SIZE = 240;

export type Sample = {
    x: Float64Array
    r1: Float64Array
    r2: Float64Array
    v1: Float64Array
    v2: Float64Array
    hash: string
}

function shuffle_array(array: any[]) {
    for (var i = array.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }
}

function buf2hex(buffer: ArrayBuffer) {
  return [...new Uint8Array(buffer)]
      .map(x => x.toString(16).padStart(2, '0'))
      .join('');
}

export class SampleLoader{
    reader: FileReader

    constructor(){
        this.reader = new FileReader();
    }

    from_file(file: File, shuffle?: boolean){
        this.reader.readAsArrayBuffer(file);

        return new Promise<Sample[]>(resolve =>  this.reader.onload = (e) => {
            const buffer = e.target?.result as ArrayBuffer;

            if (buffer) {
                let data_view = new DataView(buffer);
                let samples = [];

                for(var t = 0; t < buffer.byteLength / (8 + 5 * INPUT_SIZE * 8 + 4 * 4); t++){
                    let offset = t * (8 + 5 * INPUT_SIZE * 8 + 4 * 4);
                    let hash = buf2hex(buffer.slice(offset, offset + 8));
                    offset += 8; // hash
                    offset += 16; // ids
                    
                    let x_data = new Float64Array(INPUT_SIZE);
                    for(var i = 0; i < INPUT_SIZE; i++){
                        x_data[i] = data_view.getFloat64(offset+i*8, true);
                    }
                    offset += i*8;
                    
                    let r1_data = new Float64Array(INPUT_SIZE);
                    for(var i = 0; i < INPUT_SIZE; i++){
                        r1_data[i] = data_view.getFloat64(offset+i*8, true);
                    }
                    offset += i*8;
                    
                    let r2_data = new Float64Array(INPUT_SIZE);
                    for(var i = 0; i < INPUT_SIZE; i++){
                        r2_data[i] = data_view.getFloat64(offset+i*8, true);
                    }
                    offset += i*8;
                    
                    let v1_data = new Float64Array(INPUT_SIZE);
                    for(var i = 0; i < INPUT_SIZE; i++){
                        v1_data[i] = data_view.getFloat64(offset+i*8, true);
                    }
                    offset += i*8;
                    
                    let v2_data = new Float64Array(INPUT_SIZE);
                    for(var i = 0; i < INPUT_SIZE; i++){
                        v2_data[i] = data_view.getFloat64(offset+i*8, true);
                    }
                    offset += i*8;

                    let sample: Sample = {
                        x: x_data,
                        r1: r1_data,
                        r2: r2_data,
                        v1: v1_data,
                        v2: v2_data,
                        hash: hash
                    }
                    samples.push(sample);
                }

                if(shuffle){
                    shuffle_array(samples);
                }

                resolve(samples);
                return
            }

            throw Error("Could not load buffer.");
        });
    }
}