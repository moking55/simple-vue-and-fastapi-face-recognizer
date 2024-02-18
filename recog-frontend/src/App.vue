<template>
  <div class="container-fluid">
    <h3 class="text-center py-5">Example of face recognition</h3>
    <div class="row">
      <div class="col-12 col-md-8">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Playground</h5>
            <hr />
            <div class="row">
              <div class="col-12 col-md-6">
                <h5 class="card-title">Webcam</h5>
                <video
                  id="video"
                  width="100%"
                  height="auto"
                  :class="{ 'd-none': !showCamera }"
                ></video>
              </div>
              <div class="col-12 col-md-6">
                <h5 class="card-title">Preview</h5>
                <img :src="image" alt="Preview image" class="w-100 mb-3" />
                <div class="card">
                  <div class="card-body">
                    <h5 class="card-title">Add this person</h5>
                    <input
                      type="text"
                      class="form-control mb-2"
                      v-model="personName"
                      placeholder="Name"
                      :disabled="image === null"
                    />
                    <button
                      class="btn btn-primary mt-3 me-2"
                      @click="addPerson"
                      :disabled="image === null"
                    >
                      Add
                    </button>
                    <button class="btn btn-warning mt-3" @click="get_faces_in_database">
                      View face in database
                    </button>
                  </div>
                </div>
                <div class="card mt-3">
                  <div class="card-body">
                    <h5 class="card-title">Recoginize this person</h5>
                    <div class="d-flex align-items-center">
                      <button
                        class="btn btn-primary me-2"
                        @click="recognize"
                        :disabled="image === null"
                      >
                        Recognize
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <button class="btn btn-primary mt-3 me-2" @click="openCamera">Open Camera</button>
            <button class="btn btn-primary mt-3" @click="capture">Capture</button>
          </div>
        </div>
      </div>

      <div class="col-12 col-md-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">System status</h5>
            <p class="card-text">{{ status }}</p>
            <div class="progress" :class="{'d-none': status === 'IDLE' || status === 'ERROR'}">
              <div
                class="progress-bar progress-bar-striped progress-bar-animated"
                role="progressbar"
                aria-valuenow="100"
                aria-valuemin="0"
                aria-valuemax="100"
                style="width: 100%"
              ></div>
            </div>
          </div>
        </div>

        <div class="card mt-3">
          <div class="card-body">
            <h5 class="card-title">Train data</h5>
            <p class="card-text text-danger">
              Please add person as much as possible before training the data
            </p>
            <button class="btn btn-primary mt-3" @click="trainData">Train</button>
          </div>
        </div>

        <div class="card mt-3">
          <div class="card-body">
            <h5 class="card-title">Output</h5>
            <pre class="bg-black text-light p-2">{{ debug_output }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import axios from "axios";
export default {
  name: "App",
  data() {
    return {
      video: null,
      canvas: null,
      context: null,
      captureButton: null,
      image: null,
      showCamera: false,
      debug_output: null,
      personName: null,
      status: "IDLE"
    };
  },
  methods: {
    openCamera() {
      this.video = document.getElementById("video");
      this.showCamera = true;
      navigator.mediaDevices
        .getUserMedia({ video: true })
        .then((stream) => {
          this.video.srcObject = stream;
          this.status = "OPENING CAMERA";
          this.video.play();
        })
        .catch((err) => {
          this.status = "ERROR";
          this.debug_output = err;
        });
    },
    capture() {
      this.canvas = document.createElement("canvas");
      this.context = this.canvas.getContext("2d");
      this.video = document.getElementById("video");
      this.canvas.width = this.video.videoWidth;
      this.canvas.height = this.video.videoHeight;
      this.context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
      this.canvas.toBlob((blob) => {
        const img = new Image();
        img.src = URL.createObjectURL(blob);
        img.onload = () => {
          URL.revokeObjectURL(this.src);
        };
        this.image = img.src;
        this.status = "IDLE";
      });
      // unload camera
      this.video.srcObject.getVideoTracks().forEach((track) => {
        track.stop();
        this.showCamera = false;
      });
    },
    addPerson() {
      if (this.personName === null) {
        alert("Please enter a name");
        return;
      }
      const data = new FormData();
      this.status = "BUSY";
      // blob to base64 image string
      const blob = this.canvas.toDataURL("image/jpeg");
      data.append("base64_image", blob);
      data.append("name", this.personName);
      axios
        .post("http://localhost:8000/add", data, {
          headers: {
            "Content-Type": "multipart/form-data"
          }
        })
        .then((res) => {
          this.debug_output = res.data;
          this.status = "IDLE";
        })
        .catch((err) => {
          this.debug = err;
          this.status = "ERROR";
        });
    },
    trainData() {
      this.status = "BUSY";
      axios
        .get("http://localhost:8000/train")
        .then((res) => {
          this.debug_output = res.data;
          this.status = "IDLE";
        })
        .catch((err) => {
          this.debug = err;
          this.status = "ERROR";
        });
    },
    recognize() {
      const data = new FormData();
      const blob = this.canvas.toDataURL("image/jpeg");
      data.append("base64_image", blob);
      this.status = "BUSY";
      axios
        .post("http://localhost:8000/recognize", data, {
          headers: {
            "Content-Type": "multipart/form-data"
          }
        })
        .then((res) => {
          this.debug_output = res.data;
          this.status = "IDLE";
        })
        .catch((err) => {
          this.debug = err;
          this.status = "ERROR";
        });
    },
    get_faces_in_database() {
      this.status = "BUSY";
      axios.get("http://localhost:8000/faces").then((res) => {
        this.debug_output = res.data;
        this.status = "IDLE";
      });
    }
  }
};
</script>