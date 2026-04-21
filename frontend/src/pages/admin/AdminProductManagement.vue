<script setup>
import { computed, onMounted, reactive, ref } from "vue"
import {
  buildProductImageUrl,
  createProduct,
  deleteProduct,
  getProducts,
  updateProduct,
  uploadProductImage
} from "../../services/api"
import { getAuthSession, getAuthToken } from "../../services/auth"

const fallbackImage = "https://via.placeholder.com/400x260?text=Kulhad"

const showProductForm = ref(false)
const isEditing = ref(false)
const editingProductId = ref(null)
const isLoading = ref(true)
const isSaving = ref(false)
const isUploadingImage = ref(false)
const errorMessage = ref("")
const formError = ref("")
const searchQuery = ref("")
const products = ref([])
const session = ref(getAuthSession())
const imageInput = ref(null)
const imagePreviewUrl = ref("")
const showCategoryDropdown = ref(false)

const newProduct = reactive({
  name: "",
  category: "Kulhad",
  price: "",
  wagePerKulhad: "",
  image: ""
})

const isAdmin = computed(() => session.value?.role === "admin")
const categoryOptions = computed(() =>
  [...new Set(products.value.map((product) => (product.category || "").trim()).filter(Boolean))]
    .sort((left, right) => left.localeCompare(right))
)
const filteredCategoryOptions = computed(() => {
  const query = newProduct.category.trim().toLowerCase()

  if (!query) {
    return categoryOptions.value
  }

  return categoryOptions.value.filter((category) =>
    category.toLowerCase().includes(query)
  )
})

const filteredProducts = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return products.value.filter((product) => {
    if (!query) {
      return true
    }

    return (
      product.name.toLowerCase().includes(query) ||
      (product.category || "").toLowerCase().includes(query) ||
      String(product.price).includes(query) ||
      String(product.stock).includes(query) ||
      String(product.wage_per_kulhad).includes(query)
    )
  })
})

function resetForm() {
  newProduct.name = ""
  newProduct.category = "Kulhad"
  newProduct.price = ""
  newProduct.wagePerKulhad = ""
  newProduct.image = ""
  imagePreviewUrl.value = ""
  formError.value = ""

  if (imageInput.value) {
    imageInput.value.value = ""
  }
}

function normalizeProduct(product) {
  return {
    ...product,
    wage_per_kulhad: Number(product.wage_per_kulhad ?? 0),
    imageUrl: buildProductImageUrl(product.image) || fallbackImage,
    stock: Number(product.stock ?? 0)
  }
}

async function loadProducts() {
  isLoading.value = true
  errorMessage.value = ""

  try {
    const data = await getProducts()
    products.value = data.map(normalizeProduct)
  } catch (error) {
    errorMessage.value = error.message || "Unable to load products right now."
  } finally {
    isLoading.value = false
  }
}

function openAddProductForm() {
  if (!isAdmin.value) {
    return
  }

  isEditing.value = false
  editingProductId.value = null
  resetForm()
  showProductForm.value = true
}

function openEditProductForm(product) {
  if (!isAdmin.value) {
    return
  }

  isEditing.value = true
  editingProductId.value = product.id
  newProduct.name = product.name
  newProduct.category = product.category || "Kulhad"
  newProduct.price = product.price
  newProduct.wagePerKulhad = product.wage_per_kulhad
  newProduct.image = product.image || ""
  imagePreviewUrl.value = product.imageUrl || ""
  formError.value = ""
  showProductForm.value = true
}

function closeModal() {
  if (isSaving.value || isUploadingImage.value) {
    return
  }

  showProductForm.value = false
  showCategoryDropdown.value = false
}

function selectCategory(category) {
  newProduct.category = category
  showCategoryDropdown.value = false
}

function getPayload() {
  const payload = {
    name: newProduct.name.trim(),
    category: newProduct.category.trim(),
    price: Number(newProduct.price),
    wage_per_kulhad: Number(newProduct.wagePerKulhad),
    image: newProduct.image.trim()
  }

  if (!isEditing.value) {
    payload.stock = 0
  }

  return payload
}

async function handleImageSelected(event) {
  const file = event.target.files?.[0]

  if (!file) {
    return
  }

  const token = getAuthToken()
  if (!token) {
    formError.value = "Admin login is required to upload images."
    event.target.value = ""
    return
  }

  formError.value = ""
  isUploadingImage.value = true

  try {
    const result = await uploadProductImage(file, token)
    newProduct.image = result.filename
    imagePreviewUrl.value = buildProductImageUrl(result.filename)
  } catch (error) {
    formError.value = error.message || "Unable to upload this image."
  } finally {
    isUploadingImage.value = false
    event.target.value = ""
  }
}

function clearImage() {
  newProduct.image = ""
  imagePreviewUrl.value = ""

  if (imageInput.value) {
    imageInput.value.value = ""
  }
}

async function saveProduct() {
  formError.value = ""

  if (!newProduct.name.trim()) {
    formError.value = "Product name is required."
    return
  }

  if (!newProduct.category.trim()) {
    formError.value = "Category is required."
    return
  }

  if (newProduct.price === "" || Number(newProduct.price) < 0) {
    formError.value = "Enter a valid price."
    return
  }

  if (newProduct.wagePerKulhad === "" || Number(newProduct.wagePerKulhad) < 0) {
    formError.value = "Enter a valid wage per kulhad."
    return
  }

  const token = getAuthToken()
  if (!token) {
    formError.value = "Admin login is required to manage products."
    return
  }

  isSaving.value = true

  try {
    const payload = getPayload()

    if (isEditing.value) {
      await updateProduct(editingProductId.value, payload, token)
    } else {
      await createProduct(payload, token)
    }

    showProductForm.value = false
    await loadProducts()
  } catch (error) {
    formError.value = error.message || "Unable to save this product."
  } finally {
    isSaving.value = false
  }
}

async function removeProduct(productId) {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to delete products."
    return
  }

  try {
    await deleteProduct(productId, token)
    await loadProducts()
  } catch (error) {
    errorMessage.value = error.message || "Unable to delete this product."
  }
}

onMounted(loadProducts)
</script>

<template>
  <div class="product-management">
    <div class="page-header">
      <div class="page-copy">
        <h1>Product Management</h1>
        <p>Manage catalog pricing and define the wage per kulhad used for employee wage calculation.</p>
      </div>
      <button class="page-action" :disabled="!isAdmin" @click="openAddProductForm">
        + Add Product
      </button>
    </div>

    <div class="tabs">
      <router-link to="/admin/products" class="tab active">Products</router-link>
      <router-link to="/admin/products/history" class="tab">Log History</router-link>
    </div>

    <div v-if="!isAdmin" class="notice">
      Sign in as an admin account to create, edit, or delete products.
    </div>

    <div class="filters">
      <input v-model="searchQuery" placeholder="Search by name, category, price, wage, or stock..." />
    </div>

    <div v-if="errorMessage" class="notice error">{{ errorMessage }}</div>
    <div v-if="isLoading" class="notice">Loading products from the backend...</div>

    <div v-else class="product-grid">
      <article v-for="product in filteredProducts" :key="product.id" class="product-card">
        <img :src="product.imageUrl" :alt="product.name" class="product-image" />

        <div class="product-body">
          <div class="card-top">
            <h3>{{ product.name }}</h3>
          </div>

          <div class="info">
            <p><span>Category:</span> {{ product.category || "Kulhad" }}</p>
            <p><span>Price:</span> Rs {{ product.price }}</p>
            <p><span>Wage Per Kulhad:</span> Rs {{ product.wage_per_kulhad }}</p>
            <p><span>ID:</span> {{ product.id }}</p>
            <p><span>Image:</span> {{ product.image ? "Attached" : "No image" }}</p>
          </div>

          <div class="actions">
            <button class="adjust" :disabled="!isAdmin" @click="openEditProductForm(product)">Edit Product</button>
            <router-link class="adjust secondary" :to="{ name: 'admin-inventory' }">Manage Stock</router-link>
            <button class="icon danger" :disabled="!isAdmin" @click="removeProduct(product.id)">Delete</button>
          </div>
        </div>
      </article>
    </div>

    <div v-if="showProductForm" class="modal" @click="closeModal">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <div>
            <h3>{{ isEditing ? "Edit Product" : "Add New Product" }}</h3>
            <p>Set the product price and wage per kulhad used for employee wage calculations.</p>
          </div>
          <button type="button" class="close-btn" :disabled="isSaving || isUploadingImage" @click="closeModal">&times;</button>
        </div>

        <div class="form-grid">
          <label class="field field-full">
            <span>Product Name</span>
            <input v-model="newProduct.name" placeholder="Product Name" />
          </label>

          <label class="field">
            <span>Category</span>
            <div class="category-search">
              <input
                v-model="newProduct.category"
                placeholder="Kulhad"
                autocomplete="off"
                @focus="showCategoryDropdown = true"
                @input="showCategoryDropdown = true"
                @blur="window.setTimeout(() => { showCategoryDropdown = false }, 120)"
              />

              <div v-if="showCategoryDropdown && filteredCategoryOptions.length" class="category-dropdown">
                <button
                  v-for="category in filteredCategoryOptions"
                  :key="category"
                  type="button"
                  class="category-option"
                  @mousedown.prevent="selectCategory(category)"
                >
                  {{ category }}
                </button>
              </div>
            </div>
          </label>

          <label class="field">
            <span>Price</span>
            <input v-model.number="newProduct.price" type="number" min="0" placeholder="Price" />
          </label>

          <label class="field field-full">
            <span>Wage Per Kulhad</span>
            <input v-model.number="newProduct.wagePerKulhad" type="number" min="0" step="0.01" placeholder="Wage per kulhad" />
          </label>

          <label class="field field-full">
            <span>Upload Product Image</span>
            <input
              ref="imageInput"
              type="file"
              accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp"
              @change="handleImageSelected"
            />
            <small class="field-help">{{ isUploadingImage ? "Uploading image..." : "Choose PNG, JPG, JPEG, or WEBP." }}</small>
          </label>

          <div v-if="imagePreviewUrl" class="field field-full image-preview-wrap">
            <span>Preview</span>
            <div class="image-preview-card">
              <img :src="imagePreviewUrl" alt="Product preview" class="image-preview" />
              <button class="clear-image-btn" type="button" @click="clearImage">Remove Image</button>
            </div>
          </div>
        </div>

        <p v-if="formError" class="notice error compact">{{ formError }}</p>
        <p class="field-help inventory-note">Stock is managed in Inventory Management after the product is created.</p>

        <div class="form-actions">
          <button class="submit" :disabled="isSaving || isUploadingImage" @click="saveProduct">{{ isSaving ? "Saving..." : "Save" }}</button>
          <button class="cancel-btn" :disabled="isSaving || isUploadingImage" @click="closeModal">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.product-management { padding: 30px 50px; background: #f3ead8; min-height: 100vh; display: flex; flex-direction: column; gap: 25px; box-sizing: border-box; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.page-copy h1 { margin: 0 0 6px; }
.page-copy p { margin: 0; color: #666; }
.page-action { background: #8b4513; color: white; padding: 10px 16px; border-radius: 10px; }
.page-action:disabled, .actions button:disabled, .close-btn:disabled, .form-actions button:disabled { opacity: 0.6; cursor: not-allowed; }
.tabs { display: flex; gap: 12px; }
.tab { display: inline-flex; align-items: center; justify-content: center; padding: 8px 20px; border-radius: 20px; background: #ddd; color: inherit; text-decoration: none; }
.tab.active { background: white; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); }
.filters { display: grid; grid-template-columns: 1fr; gap: 15px; }
.filters input { padding: 12px; border-radius: 10px; border: 1px solid #ddd; background: white; }
.notice { padding: 14px 16px; border-radius: 10px; background: #fff7ed; color: #9a3412; border: 1px solid #fdba74; }
.notice.error { background: #fef2f2; color: #b91c1c; border-color: #fca5a5; }
.notice.compact { margin: 0; }
.product-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }
.product-card { overflow: hidden; border-radius: 14px; background: #fffdf9; border: 1px solid #eadfcb; box-shadow: 0 10px 22px rgba(95, 56, 23, 0.08); }
.product-image { width: 100%; height: 210px; object-fit: cover; display: block; }
.product-body { display: flex; flex-direction: column; gap: 12px; padding: 22px; background: linear-gradient(180deg, #fffdf9 0%, #fbf6ee 100%); }
.card-top { display: flex; align-items: center; gap: 12px; }
.card-top h3 { margin: 0; }
.info { margin: 2px 0 0; }
.info p { margin: 0 0 8px; }
.info span { color: #777; }
.actions { display: flex; gap: 10px; margin-top: 4px; align-items: stretch; }
.adjust { flex: 1; padding: 10px; border-radius: 10px; background: #f1f1f1; text-align: center; text-decoration: none; color: inherit; }
.adjust.secondary { background: #fff7ed; border: 1px solid #f3d2a8; color: #8b4513; }
.icon { padding: 10px; border-radius: 8px; background: #eee; }
.icon.danger { background: #fee2e2; color: #b42318; }
.modal { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; padding: 20px; z-index: 1000; }
.modal-box { width: min(640px, 100%); padding: 24px; border-radius: 18px; background: linear-gradient(180deg, #fffdf9 0%, #f8f2e8 100%); box-shadow: 0 24px 48px rgba(0, 0, 0, 0.18); }
.modal-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 20px; }
.modal-header h3 { margin: 0 0 6px; }
.modal-header p { margin: 0; color: #666; font-size: 14px; }
.close-btn { border: none; background: transparent; cursor: pointer; font-size: 24px; line-height: 1; padding: 0; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.field { display: flex; flex-direction: column; gap: 7px; }
.category-search { position: relative; width: 100%; }
.category-search input { width: 100%; box-sizing: border-box; }
.category-dropdown { position: absolute; top: calc(100% + 6px); left: 0; right: 0; z-index: 5; max-height: 180px; overflow-y: auto; border: 1px solid #ddd; border-radius: 10px; background: white; box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12); }
.category-option { width: 100%; border: none; border-bottom: 1px solid #f1ede6; background: white; padding: 10px 12px; text-align: left; font: inherit; color: #3b2a18; cursor: pointer; }
.category-option:last-child { border-bottom: none; }
.category-option:hover { background: #fff7ed; }
.field-full { grid-column: 1 / -1; }
.field span { font-size: 13px; font-weight: 600; color: #5f3817; }
.field input, .field textarea, .field select { padding: 11px 12px; border: 1px solid #ddd; border-radius: 10px; background: white; font: inherit; }
.field-help { color: #7c6a58; font-size: 12px; }
.inventory-note { margin: 10px 0 0; }
.image-preview-wrap { gap: 10px; }
.image-preview-card { display: flex; align-items: flex-start; gap: 14px; padding: 14px; border-radius: 14px; background: #fffaf2; border: 1px solid #eadfcb; }
.image-preview { width: 120px; height: 120px; object-fit: cover; border-radius: 12px; }
.clear-image-btn { padding: 10px 12px; border-radius: 10px; background: white; border: 1px solid #d6c7b1; color: #5f3817; }
.form-actions { display: flex; gap: 10px; margin-top: 18px; }
.form-actions button { flex: 1; padding: 10px 12px; border-radius: 10px; }
.submit { background: #8b4513; color: white; }
.cancel-btn { background: white; border: 1px solid #d6c7b1; color: #5f3817; }
@media (max-width: 1100px) { .product-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 900px) { .product-management { padding: 24px; } .page-header, .modal-header, .image-preview-card { flex-direction: column; } }
@media (max-width: 640px) { .product-management { padding: 20px; } .tabs, .actions, .form-actions { flex-wrap: wrap; } .product-grid, .form-grid { grid-template-columns: 1fr; } }
</style>
