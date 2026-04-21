<template>
  <div class="image-uploader">
    <label class="upload-btn">
      Take Photo
      <input
        type="file"
        accept="image/*"
        capture="environment"
        @change="onFileChange"
        hidden
      />
    </label>

    <label class="upload-btn upload-btn--secondary">
      Upload Image
      <input
        type="file"
        accept="image/*"
        @change="onFileChange"
        hidden
      />
    </label>

    <p v-if="fileError" class="error">Please select a valid image.</p>
  </div>
</template>

<script setup>
import { defineEmits, ref } from "vue"

const emit = defineEmits(["image-selected"])
const fileError = ref("")

function onFileChange(event) {
  fileError.value = ""
  const input = event.target

  if (!input.files || input.files.length === 0) {
    fileError.value = "No file selected."
    return
  }

  const file = input.files[0]
  if (!file.type.startsWith("image/")) {
    fileError.value = "Selected file is not an image."
    return
  }

  const reader = new FileReader()
  reader.onload = () => {
    emit("image-selected", file, reader.result)
    input.value = ""
  }
  reader.readAsDataURL(file)
}
</script>

<style scoped>
.image-uploader {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 150px;
  padding: 10px 16px;
  border-radius: 10px;
  background: #8b4513;
  color: white;
  cursor: pointer;
  font-weight: 500;
  transition: 0.2s ease;
}

.upload-btn:hover {
  opacity: 0.92;
}

.upload-btn--secondary {
  background: #ede2cf;
  color: #5f3817;
}

.error {
  width: 100%;
  margin: 0;
  color: #c2410c;
}
</style>
