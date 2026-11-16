package bnbemu.handler.shop
import bnbemu.netty.PKTHandler
import bnbemu.packet.UserItemUpdate
import bnbemu.server.LocalShop
val UserItemListReq = PKTHandler { c ->
    c.users.take(2).forEachIndexed { player,user ->
        LocalShop.store.account(user.accountKey).items.forEach { (id, count) ->
            c send UserItemUpdate(slotType=player,itemId = id, quantity = count)
        }
    }
}
