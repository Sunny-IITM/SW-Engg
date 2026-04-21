<template>

<div>

<button
v-for="cat in categories"
:key="cat"
class="btn btn-outline-dark me-2"
@click="$emit('filter',cat)"
>

{{cat}}

</button>

</div>

</template>

<script>

export default{
props:["categories"]
}

</script>