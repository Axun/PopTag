package bnbemu.netty

import bnbemu.packet.*
import bnbemu.server.*
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import java.nio.file.Path

class FaceEmotionImportTest {
    @TempDir lateinit var directory: Path

    @Test fun boundedBatchExposesFacesBasicExpressionsAndAccessoriesWithTheirRealCategories() {
        val added = ItemDef.DEFAULT_ITEMS.filter { it.itemId in 970_000_000 until 980_000_000 }
        assertEquals(52,added.count { it.category == 3 })
        assertTrue(added.count { it.category == 19 } >= 16,"Retain the original sixteen faces alongside expanded clothing")
        assertEquals(12,added.count { it.category == 12 })
        val catalog = ShopCatalog.decodeBlock(ShopCatalog.buildBlock(ShopCatalog.DEFAULT_ITEMS))
        for (item in added) {
            val product = catalog.single { it.itemId == item.itemId }
            assertEquals(item.category, product.category)
            assertEquals(item.desc, product.name)
            assertTrue(product.tail.price1 > 0)
            assertTrue(item.desc.any { it in '\u3400'..'\u9fff' })
        }
        assertTrue(added.filter { it.category == 19 }.map { it.skinId }.toSet().containsAll(setOf(5,6)))
        assertTrue(added.filter { it.category == 19 }.all { it.skinId in 0..7 && it.targetCharId in 0..8 && it.name == "Item/AvatarDeco" })
        for (character in 0..7) {
            val expressions=added.filter { it.category == 3 && it.skinId == character }
            assertEquals(if(character in setOf(5,6)) (0..7).toSet() else setOf(0,1), expressions.map { it.targetCharId }.toSet())
            assertEquals(if(character in setOf(5,6)) 20 else 2, expressions.size)
        }
    }

    @Test fun itemEnvelopeSurvivesTheSixtyFourKilobyteBoundaryAndRejectsTruncation() {
        // Use an independent stress table; don't assume the real translated
        // catalog is already large enough to exercise its third length byte.
        val template = ItemDef.DEFAULT_ITEMS.first()
        val stress = ItemDef.DEFAULT_ITEMS + (0 until 256).map {
            template.copy(itemId = 1_000_000_000 + it, desc = "长度边界验证样本".repeat(4))
        }
        val block = ItemDef.buildBlock(stress)
        assertTrue(block.size > 65536)
        val length = (block[1].toInt() and 255) or ((block[2].toInt() and 255) shl 8) or ((block[3].toInt() and 255) shl 16)
        assertEquals(block.size - 5, length)
        assertEquals(stress, ItemDef.decodeBlock(block))
        assertThrows(IllegalArgumentException::class.java) { ItemDef.decodeBlock(block.copyOf(block.size-1)) }
    }

    @Test fun purchasedFaceAndExpressionKeepTheirResourcesAfterSavingAndReloading() {
        val store = LocalShopStore(directory)
        store.reward("face-emote-test", "fixture-funds", LocalEconomy.Reward(40000000,0))
        for (category in listOf(19,3)) {
            val item = ItemDef.DEFAULT_ITEMS.first { it.itemId in 970_000_000 until 980_000_000 && it.category == category && it.skinId == 6 }
            val product = ShopCatalog.DEFAULT_ITEMS.single { it.itemId == item.itemId }
            assertEquals(PurchaseStatus.OK, store.purchase("face-emote-test",product).status)
            val restored = LocalShopStore(directory).account("face-emote-test")
            val entry = localInventoryEntries(restored,0,emptyList()).single { it.itemId == item.itemId }
            assertEquals(item.name,entry.token)
            assertTrue(entry.expireDate.all { it==0.toByte() })
        }
        assertFalse(ShopCatalog.DEFAULT_ITEMS.any { product ->
            ItemDef.DEFAULT_ITEMS.any { it.itemId == product.itemId && it.category == 14 && it.param == 134 }
        })
        assertTrue(ItemDef.DEFAULT_ITEMS.any { it.category == 14 && it.param == 134 })
    }
}
