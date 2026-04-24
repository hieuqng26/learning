<script setup>
const logoUrl = import.meta.env.VITE_LOGO_URL
const appName = import.meta.env.VITE_FOOTER
</script>

<template>
  <div class="layout-footer">
    <img :src="logoUrl" alt="Logo" height="20" class="mr-2" />
    by
    <span class="text-lg ml-2">{{ appName }}</span>
  </div>
</template>
<style lang="scss" scoped></style>
