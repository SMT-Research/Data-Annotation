import { SampleLoader, type Sample } from "./samples";
import Chart from 'chart.js/auto';

const file_input = document.getElementById("file-input") as HTMLElement;
const file_input_display = document.getElementById("file-input-display") as HTMLElement;
const status_label = document.getElementById("status-label") as HTMLElement;
const moisture_label = document.getElementById("moisture-label") as HTMLElement;
const counter = document.getElementById("counter") as HTMLInputElement;
const download = document.getElementById("download") as HTMLInputElement;

const resistance_canvas = document.getElementById("resistance-chart") as HTMLCanvasElement;
const voltage_canvas = document.getElementById("voltage-chart") as HTMLCanvasElement;

type Annotation = {
    status: "pass" | "observe" | "fail" | "checksum"
    is_dry: boolean
    hash: string
}

type WeatherData = {
    daily: {
        rain_sum: number[]
        snowfall_sum: number[]
        time: number[]
    }
}

const sample_loader = new SampleLoader();
const charts = [{canvas: resistance_canvas, type: "r"}, {canvas: voltage_canvas, type: "v"}].map(({canvas, type}) => (
    new Chart(canvas, {
        type: "line",
        data: {
            datasets: [
                { data: [{x: 0, y: 0}], pointRadius: 0, yAxisID: "y", borderColor: type == "r" ? "#c7b830ff" : "#ff4141ff", backgroundColor: type == "r" ? "#c7b830ff" : "#ff4141ff" },
                { data: [{x: 0, y: 0}], pointRadius: 0, yAxisID: "y", borderColor: type == "r" ? "#083dafff" : "#000000ff", backgroundColor: type == "r" ? "#083dafff" : "#000000ff" },
                {
                    type: "bar",
                    data: [{x: 0, y: 0}],
                    barPercentage: 1,
                    categoryPercentage: 1,
                    backgroundColor: "rgba(54, 162, 235, 0.45)",
                    yAxisID: "y1"
                }
            ]
        },
        options: {
            maintainAspectRatio: false,
            animation: false,
            interaction: {
                mode: "nearest",
                intersect: false
            },
            layout: {
                padding: {
                    left: 30,
                    right: 15,
                    top: 20,
                    bottom: 20
                }
            },
            scales: {
                x: {
                    type: "linear",
                    ticks: {
                        callback: (t) => t
                    },
                },
                y: {
                    type: "linear",
                    position: "left",
                    max: type == "v" ? 5100000 : undefined,
                    min: type == "v" ? -100000 : 0,
                    ticks: {
                        stepSize: 2500000 / 2
                    }
                },
                y1: {
                    type: "linear",
                    position: "right",
                    grid: { display: false }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    })
))
var samples: Sample[] = [];
var current_graph_index = -1;
var annotations: {[key: string]: Annotation} = {}
var file_name: string = "null";
var weather: WeatherData | null = null;

let stored_annotations = localStorage.getItem("annotations");
if(stored_annotations !== null){
    annotations = JSON.parse(stored_annotations);
    console.log(`Loaded ${Object.keys(annotations).length} annotations from localStorage.`);
}

document.addEventListener('keydown', function(event) {
    if(event.code == "Space"){
        if(current_graph_index < samples.length-1){
            let annotation = get_annotation();
            if(annotation != null){
                annotations[samples[current_graph_index].hash] = annotation;

                // current_graph_index++;
                for(var i = current_graph_index; i < samples.length; i++){
                    if(!annotations[samples[i].hash]){
                        break;
                    }
                }
                current_graph_index = Math.min(i, samples.length-1);
                show_sample_index(current_graph_index);
            }
        }
    }
    if(event.code == "KeyH"){
        update_status("pass");
    }else if(event.code == "KeyJ"){
        update_status("observe");
    }else if(event.code == "KeyK"){
        update_status("fail");
    }else if(event.code == "KeyL"){
        update_status("checksum");
    }else if(event.code == "KeyM"){
        toggle_moisture();
    }

    if(event.code == "ControlLeft"){
        current_graph_index = Math.max(0, current_graph_index - 1);
        show_sample_index(current_graph_index);
    }
});

counter.addEventListener("input", () => {
    let value = Number(counter.value);
    if(value >= 0 && value < samples.length){
        show_sample_index(value);
    }
})

counter.addEventListener("focusout", () => {
    show_sample_index(current_graph_index);
})

download.addEventListener("click", () => {
    let data: any = {};
    samples.forEach(sample => {
        if(annotations[sample.hash]){
            data[sample.hash] = annotations[sample.hash];
        }
    });
    download_custom_data(file_name + "_annotations.json", JSON.stringify(data), "application/json")
})

function download_custom_data(filename: string, data: string, mimeType: string) {
    const blob = new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    setTimeout(() => {URL.revokeObjectURL(url)}, 1000);
}

function set_annotation(annotation: Annotation){
    update_status(annotation.status);
    toggle_moisture(annotation.is_dry);
}

function on_drag_over(e: DragEvent){
    e.preventDefault();
    file_input_display.classList.add("over");
}

function update_counter(){
    counter.value = Math.max(0, current_graph_index).toString();
}

function update_status(status: "pass" | "observe" | "fail" | "checksum" | "none"){
    status_label.classList.remove("pass");
    status_label.classList.remove("observe");
    status_label.classList.remove("fail");
    status_label.classList.remove("checksum");
    if(status != "none") status_label.classList.add(status);
    status_label.innerText = {
        "pass": "Pass",
        "observe": "Observe",
        "fail": "Fail",
        "none": "...",
        "checksum": "Checksum"
    }[status]
}

function toggle_moisture(to?: boolean){
    if(to != undefined){
        to ? moisture_label.classList.remove("wet") : moisture_label.classList.add("wet");;
    }else{
        moisture_label.classList.toggle("wet");
    }
    moisture_label.innerText = "Dry";
    if(moisture_label.classList.contains("wet")){
        moisture_label.innerText = "Wet";
    }
}

function get_annotation(): Annotation | null {
    let status: string | null = Array.from(status_label.classList).filter(x => ["pass", "observe", "fail", "checksum"].includes(x))[0];
    let is_dry = !moisture_label.classList.contains("wet");
    if(status == undefined) return null;
    return {
        status: status as "pass" | "observe" | "fail" | "checksum",
        is_dry,
        hash: samples[current_graph_index].hash
    }
}

function show_sample_index(idx: number){
    show_sample(samples[idx]);
    current_graph_index = idx;
    update_counter();
    if(Object.keys(annotations).includes(samples[idx].hash)){
        set_annotation(annotations[samples[idx].hash]);
    }else{
        update_status("none");
        toggle_moisture(false);
    }
}

function show_sample(sample: Sample){
    let r1 = [...sample.x].map((x, i) => ({
        x: (x - sample.x[0]) / 86400,
        y: sample.r1[i],
    }))
    let r2 = [...sample.x].map((x, i) => ({
        x: (x - sample.x[0]) / 86400,
        y: sample.r2[i],
    }))
    let v1 = [...sample.x].map((x, i) => ({
        x: (x - sample.x[0]) / 86400,
        y: sample.v1[i],
    }))
    let v2 = [...sample.x].map((x, i) => ({
        x: (x - sample.x[0]) / 86400,
        y: sample.v2[i],
    }))
    charts[0].data.datasets[0].data = r1;
    charts[0].data.datasets[1].data = r2;
    charts[1].data.datasets[0].data = v1;
    charts[1].data.datasets[1].data = v2;
    
    if(weather){
        let weather_slice = weather.daily.time.map((x, i) => ({
            x: (x - sample.x[0]) / 86400,
            y: weather?.daily.rain_sum[i] as number
        }));
        let filtered = weather_slice.filter(p => p.x >= 0 && p.x <= 30);
        charts[0].data.datasets[2].data = filtered;
        charts[1].data.datasets[2].data = filtered;
    }

    charts[0].update();
    charts[1].update();
}

function on_drop(e: DragEvent){
    e.preventDefault();
    file_input_display.classList.remove("over");

    if(e.dataTransfer){
        [...e.dataTransfer.items].forEach(async item => {
            console.log(item);
            let file = item.getAsFile()
            if(file){
                file_name = file.name;
                samples = await sample_loader.from_file(file, false);
                for(var i = 0; i < samples.length; i++){
                    if(!annotations[samples[i].hash]){
                        break;
                    }
                }
                show_sample_index(Math.min(i, samples.length-1));

                file_input.hidden = true;
            }
        })
    }
}

file_input.addEventListener("dragover", on_drag_over)
file_input.addEventListener("drop", on_drop);

(async () => {
    let r = await fetch("weather.json");
    let data = await r.json() as WeatherData;
    data.daily.time = (data.daily.time as unknown as string[]).map(x => new Date(x).getTime() / 1000);
    weather = data;
})()

setInterval(() => {
    localStorage.setItem("annotations", JSON.stringify(annotations));
    console.log("Saved.");
}, 30000)