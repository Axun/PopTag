package bnbemu.netty

import bnbemu.packet.ItemDef
import bnbemu.packet.ShopCatalog
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class BulkShopImportTest {
    @Test fun fullNationalBatchSurvivesCatalogEncodingWithGoldPricesAndOriginalNames() {
        val imports=requireNotNull(javaClass.getResourceAsStream("/data/shop-import-20261116.tsv"))
            .bufferedReader().useLines { lines -> lines.filterNot { it.startsWith("#") || it.isBlank() }.map { it.split('\t') }.toList() }
        assertEquals(2607,imports.size,"This batch is a retained publication baseline, not a cap on future imports")
        val definitionBlock=ItemDef.buildBlock(ItemDef.DEFAULT_ITEMS)
        val definitions=ItemDef.decodeBlock(definitionBlock).associateBy { it.itemId }
        val catalogBlock=ShopCatalog.buildBlock(ShopCatalog.DEFAULT_ITEMS)
        val catalog=ShopCatalog.decodeBlock(catalogBlock)
        assertTrue(definitionBlock.size>65536)
        assertTrue(catalogBlock.size>65536)
        assertEquals(catalog.size,catalog.map { it.prodId }.toSet().size)
        val products=catalog.groupBy { it.itemId }
        for(row in imports) {
            val id=row[0].toInt();val category=row[1].toInt();val name=row[3]
            assertEquals(category,requireNotNull(definitions[id]).category)
            val product=requireNotNull(products[id]) { "Missing imported product $name ($id)" }.single()
            assertEquals(category,product.category)
            assertEquals(name,product.name)
            assertEquals(1,product.count)
            assertEquals(1,product.tail.f9)
            assertTrue(product.tail.price1 in 120000..880000,"$name must keep normal consumable gold pricing")
        }
    }
}
