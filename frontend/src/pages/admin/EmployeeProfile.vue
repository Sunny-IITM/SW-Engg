<script setup>
import { onMounted, reactive, ref } from "vue"
import { getMyProfile, updateMyProfile } from "../../services/api"
import { getAuthSession, getAuthToken, updateAuthSession } from "../../services/auth"

const session = ref(getAuthSession())
const token = getAuthToken()
const isLoading = ref(false)
const isSaving = ref(false)
const message = ref("")
const errorMessage = ref("")

const profile = reactive({
  name: session.value?.name || "",
  email: session.value?.email || "",
  phone: session.value?.phone || "",
  address: session.value?.address || "",
  department: session.value?.department || "",
  jobTitle: session.value?.job_title || ""
})

const passwordForm = reactive({
  currentPassword: "",
  newPassword: "",
  confirmPassword: ""
})

async function loadProfile() {
  if (!token) {
    errorMessage.value = "Employee login is required to view the profile."
    return
  }

  isLoading.value = true
  errorMessage.value = ""

  try {
    const response = await getMyProfile(token)
    profile.name = response.name || ""
    profile.email = response.email || ""
    profile.phone = response.phone || ""
    profile.address = response.address || ""
    profile.department = response.department || ""
    profile.jobTitle = response.job_title || ""

    session.value = updateAuthSession({
      name: response.name || "",
      email: response.email || "",
      phone: response.phone || "",
      address: response.address || "",
      department: response.department || "",
      job_title: response.job_title || ""
    })
  } catch (error) {
    errorMessage.value = error.message || "Unable to load employee profile."
  } finally {
    isLoading.value = false
  }
}

async function saveProfile() {
  if (!token) {
    errorMessage.value = "Employee login is required to update the profile."
    return
  }

  isSaving.value = true
  errorMessage.value = ""
  message.value = ""

  try {
    const response = await updateMyProfile({
      name: profile.name.trim(),
      phone: profile.phone.trim(),
      address: profile.address.trim()
    }, token)

    session.value = updateAuthSession({
      name: response.name || "",
      email: response.email || "",
      phone: response.phone || "",
      address: response.address || "",
      department: response.department || "",
      job_title: response.job_title || ""
    })
    message.value = "Profile updated successfully."
  } catch (error) {
    errorMessage.value = error.message || "Unable to update employee profile."
  } finally {
    isSaving.value = false
  }
}

async function resetPassword() {
  if (!token) {
    errorMessage.value = "Employee login is required to update the password."
    return
  }

  if (!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
    errorMessage.value = "Fill all password fields."
    return
  }

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    errorMessage.value = "New passwords do not match."
    return
  }

  isSaving.value = true
  errorMessage.value = ""
  message.value = ""

  try {
    await updateMyProfile({
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword
    }, token)
    passwordForm.currentPassword = ""
    passwordForm.newPassword = ""
    passwordForm.confirmPassword = ""
    message.value = "Password updated successfully."
  } catch (error) {
    errorMessage.value = error.message || "Unable to update password."
  } finally {
    isSaving.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <section class="employee-profile-page">
    <div class="hero">
      <div>
        <p class="eyebrow">Employee Profile</p>
        <h1>{{ profile.name || "Employee" }}</h1>
        <p class="subcopy">Review your role details and keep your personal contact information up to date.</p>
      </div>

      <div class="role-card">
        <span>{{ profile.jobTitle || "Team Member" }}</span>
        <strong>{{ profile.department || "Department not set" }}</strong>
      </div>
    </div>

    <div v-if="errorMessage" class="notice error">{{ errorMessage }}</div>
    <div v-if="message" class="notice success">{{ message }}</div>
    <div v-if="isLoading" class="notice">Loading employee profile...</div>

    <div v-else class="profile-layout">
      <article class="profile-card summary">
        <h2>Profile Summary</h2>
        <div class="summary-list">
          <p><span>Name</span>{{ profile.name || "Not set" }}</p>
          <p><span>Email</span>{{ profile.email || "Not set" }}</p>
          <p><span>Phone</span>{{ profile.phone || "Not set" }}</p>
          <p><span>Address</span>{{ profile.address || "Not set" }}</p>
          <p><span>Department</span>{{ profile.department || "Not set" }}</p>
          <p><span>Job Title</span>{{ profile.jobTitle || "Not set" }}</p>
          <p><span>Compensation</span>Product-based wages from Product Management settings</p>
        </div>
      </article>

      <article class="profile-card form-card">
        <div class="card-header">
          <div>
            <h2>Edit Profile</h2>
            <p>Update your name, email, phone, and address here.</p>
          </div>
        </div>

        <form class="profile-form" @submit.prevent="saveProfile">
          <label class="field">
            <span>Full Name</span>
            <input v-model="profile.name" placeholder="Your full name" />
          </label>

          <label class="field">
            <span>Email</span>
            <input v-model="profile.email" type="email" placeholder="name@example.com" disabled />
          </label>

          <label class="field">
            <span>Phone</span>
            <input v-model="profile.phone" placeholder="+91 98765 43210" />
          </label>

          <label class="field field-full">
            <span>Address</span>
            <textarea v-model="profile.address" rows="4" placeholder="House number, street, area, city"></textarea>
          </label>

          <label class="field">
            <span>Department</span>
            <input :value="profile.department || 'Not set'" disabled />
          </label>

          <label class="field">
            <span>Job Title</span>
            <input :value="profile.jobTitle || 'Not set'" disabled />
          </label>

          <label class="field field-full">
            <span>Compensation Model</span>
            <input :value="'Performance-based and driven by product wage settings in Product Management'" disabled />
          </label>

          <button class="save-btn" type="submit" :disabled="isSaving">
            {{ isSaving ? "Saving..." : "Save Profile" }}
          </button>
        </form>
      </article>

      <article class="profile-card form-card">
        <div class="card-header">
          <div>
            <h2>Reset Password</h2>
            <p>Use your current password to set a new one.</p>
          </div>
        </div>

        <form class="profile-form" @submit.prevent="resetPassword">
          <label class="field">
            <span>Current Password</span>
            <input v-model="passwordForm.currentPassword" type="password" />
          </label>

          <label class="field">
            <span>New Password</span>
            <input v-model="passwordForm.newPassword" type="password" />
          </label>

          <label class="field field-full">
            <span>Confirm New Password</span>
            <input v-model="passwordForm.confirmPassword" type="password" />
          </label>

          <button class="save-btn" type="submit" :disabled="isSaving">
            {{ isSaving ? "Saving..." : "Update Password" }}
          </button>
        </form>
      </article>
    </div>
  </section>
</template>

<style scoped>
.employee-profile-page {
  min-height: 100vh;
  padding: 30px;
  background: #f3ead8;
}
.hero { display: flex; justify-content: space-between; gap: 20px; align-items: flex-start; margin-bottom: 24px; }
.eyebrow { margin: 0 0 8px; color: #9a3412; font-size: 13px; font-weight: 700; text-transform: uppercase; }
.hero h1 { margin: 0; color: #4a2910; }
.subcopy { margin: 10px 0 0; color: #6f604e; max-width: 680px; }
.role-card { min-width: 220px; padding: 18px 20px; border-radius: 16px; background: white; box-shadow: 0 10px 24px rgba(95, 56, 23, 0.08); display: grid; gap: 8px; }
.role-card span { color: #8b4513; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.role-card strong { color: #4a2910; }
.notice { padding: 14px 16px; border-radius: 10px; margin-bottom: 18px; }
.notice.success { background: #ecfdf3; color: #166534; border: 1px solid #86efac; }
.notice.error { background: #fef2f2; color: #b91c1c; border: 1px solid #fca5a5; }
.profile-layout { display: grid; grid-template-columns: 320px 1fr; gap: 22px; }
.profile-card { padding: 24px; border-radius: 18px; background: white; box-shadow: 0 10px 24px rgba(95, 56, 23, 0.08); }
.profile-card h2 { margin: 0 0 16px; color: #4a2910; }
.summary-list { display: grid; gap: 14px; }
.summary-list p { margin: 0; display: grid; gap: 4px; color: #5f3817; }
.summary-list span { font-size: 12px; color: #9a3412; font-weight: 700; text-transform: uppercase; }
.card-header p { margin: 6px 0 0; color: #6f604e; }
.profile-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.field { display: grid; gap: 8px; }
.field-full { grid-column: 1 / -1; }
.field span { font-size: 13px; font-weight: 700; color: #5f3817; }
.field input, .field textarea { width: 100%; box-sizing: border-box; padding: 12px 14px; border: 1px solid #ddd5c6; border-radius: 10px; background: white; font: inherit; }
.field textarea { resize: vertical; }
.field input:disabled { background: #f7f4ee; color: #7a6a57; }
.save-btn { grid-column: 1 / -1; justify-self: start; padding: 12px 18px; border: none; border-radius: 10px; background: #8b4513; color: white; font-weight: 700; }
@media (max-width: 980px) { .profile-layout { grid-template-columns: 1fr; } }
@media (max-width: 720px) { .employee-profile-page { padding: 20px; } .hero { flex-direction: column; } .profile-form { grid-template-columns: 1fr; } }
</style>
