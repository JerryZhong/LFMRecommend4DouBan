LFMRecommend4DouBan
===================

针对豆瓣图书的LFM推荐程序。

LFM算法参考 http://sifter.org/~simon/journal/20061211.html 或《推荐系统实践》
（http://book.douban.com/subject/10769749/）。

由于豆瓣禁止数据爬虫的大量抓取，基础数据取自
http://www.datatang.com/data/42832/。

目标：
 * 对于权重较大的用户、图书信息采用爬虫抓取实时信息。
 * 使用GPU加速计算
 * 尽量减少群体评分偏移和个人评分偏移的影响。
 * 其他算法上的优化。