<template>

<div class="row product-grid">

<div
class="col-md-4 mb-4 d-flex"
v-for="product in products"
:key="product.id"
>

<ProductCard :product="product" @added-to-cart="$emit('added-to-cart', $event)"/>

</div>

</div>

</template>

<script>

import ProductCard from "./ProductCard.vue"

export default{

props:["products"],
emits:["added-to-cart"],

components:{
ProductCard
}

}

</script>

<style scoped>
.product-grid > [class*="col-"] {
  align-items: stretch;
}

.product-grid :deep(.product-card) {
  width: 100%;
}
</style>
