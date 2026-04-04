import { defineStore } from 'pinia'
import { fetchCategoriesByProduct, fetchProducts } from '../services/catalogService'

export const useCatalogStore = defineStore('catalog', {
  state: () => ({
    products: [],
    categoriesByProduct: {},
    productsError: '',
    categoriesErrorByProduct: {},
    isLoadingProducts: false,
    isLoadingCategories: false,
    productsLastLoadedAt: 0,
  }),

  actions: {
    async loadProducts({ force = false } = {}) {
      if (!force && this.products.length) return this.products
      if (this.isLoadingProducts) return this.products
      this.isLoadingProducts = true
      this.productsError = ''
      try {
        this.products = await fetchProducts()
        this.productsLastLoadedAt = Date.now()
        return this.products
      } catch (error) {
        this.products = []
        this.productsLastLoadedAt = 0
        this.productsError = error?.message || 'No fue posible cargar los tickets.'
        return []
      } finally {
        this.isLoadingProducts = false
      }
    },

    async loadCategoriesForProduct(productId) {
      if (this.categoriesByProduct[productId]) return this.categoriesByProduct[productId]

      this.isLoadingCategories = true
      this.categoriesErrorByProduct = {
        ...this.categoriesErrorByProduct,
        [productId]: '',
      }
      try {
        const categories = await fetchCategoriesByProduct(productId)
        this.categoriesByProduct[productId] = categories
        return categories
      } catch (error) {
        this.categoriesByProduct[productId] = []
        this.categoriesErrorByProduct = {
          ...this.categoriesErrorByProduct,
          [productId]: error?.message || 'No fue posible cargar las categorías.',
        }
        return []
      } finally {
        this.isLoadingCategories = false
      }
    },
  },
})
