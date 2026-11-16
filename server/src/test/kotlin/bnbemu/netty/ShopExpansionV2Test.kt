package bnbemu.netty

import bnbemu.packet.ItemDef
import bnbemu.packet.ShopCatalog
import bnbemu.server.LocalShopStore
import bnbemu.server.PurchaseStatus
import bnbemu.server.localInventoryEntries
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import java.nio.file.Path

class ShopExpansionV2Test {
    @TempDir lateinit var directory: Path

    // Fixed publication batch: this verifies real catalog wiring and saved ownership,
    // rather than merely checking the input TSV against itself.
    private val names = listOf("都敏俊教授装", "宝宝绿围巾", "燕尾服", "心动时分", "古老的院子", "守望者", "2007年10段账号效果")

    @Test fun nationalCosmeticsArePurchasableWithGoldAndSurviveStoreReloadWithoutDuplicatedEquipment() {
        val products=names.map { name -> requireNotNull(ShopCatalog.DEFAULT_ITEMS.firstOrNull { it.name==name }) { "Missing product $name" } }
        assertEquals(setOf(10,18,19),products.map { it.category }.toSet())
        for((index,p) in products.withIndex()) {
            val user="expansion-$index"
            assertTrue(p.tail.price1 in 120000..680000)
            assertEquals(1,p.tail.f9,"Gold purchase flag")
            val store=LocalShopStore(directory)
            val bought=store.purchase(user,p)
            assertEquals(PurchaseStatus.OK,bought.status)
            assertEquals(3000000-p.tail.price1,bought.account.lucci)
            assertEquals(1,bought.account.items[p.itemId])
            store.changeEquipment(user,0,listOf(100 to p.itemId))
            val persisted=LocalShopStore(directory).account(user)
            assertEquals(p.itemId,persisted.equipment[0]?.get(100))
            assertEquals(1,localInventoryEntries(persisted,0,emptyList()).count { it.itemId==p.itemId })
            assertEquals(1,ShopCatalog.DEFAULT_ITEMS.count { it.itemId==p.itemId },"No duplicate catalog row")
        }
        assertTrue(ItemDef.DEFAULT_ITEMS.any { it.category==19 && it.skinId==6 && it.targetCharId==2 })
        assertTrue(ItemDef.DEFAULT_ITEMS.any { it.category==19 && it.skinId==5 && it.targetCharId==2 })
    }
}
