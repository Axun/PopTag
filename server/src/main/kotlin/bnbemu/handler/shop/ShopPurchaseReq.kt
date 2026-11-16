package bnbemu.handler.shop
import bnbemu.netty.*
import bnbemu.packet.*
import bnbemu.server.*
/** Verified EN op267 body: E4(product id), E4(option), E1(payment mode). */
val ShopPurchaseReq = PKTHandler { c ->
    val user = c.users.getOrNull(c.shopPlayerIndex) ?: return@PKTHandler
    if (readableBytes() != 9) { c send ShopPurchaseResult(false); return@PKTHandler }
    val productId = Decode4
    val option = Decode4
    val payment = Decode1
    // Only the observed Lucci path is supported. Never trust client-side prices.
    if (option != 0 || payment != 0) { c send ShopPurchaseResult(false); return@PKTHandler }
    val product = ShopCatalog.DEFAULT_ITEMS.firstOrNull { it.prodId == productId }
    try {
        val result = LocalShop.store.purchase(user.accountKey, product)
        val success = result.status == PurchaseStatus.OK
        user.lucci = result.account.lucci
        c send ShopPurchaseResult(success)
        if (success) {
            c send UserDynamicInfo(c.shopPlayerIndex, user.lucci)
            // S202 success already creates/updates the purchased stock through
            // native 66B4ED -> 66A017 -> 65D281. A second S274 stock insertion
            // leaves a duplicate in the open shop/profile until a full refresh.
            // Login/list sync still sends authoritative ownership separately.
        }
        println("[LocalPurchase] product=$productId status=${result.status} balance=${user.lucci}")
    } catch (e: java.io.IOException) {
        c send ShopPurchaseResult(false)
        System.err.println("[LocalPurchase] save failed: ${e.javaClass.simpleName}")
    }
}
