// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'database.dart';

// ignore_for_file: type=lint
class $CachedOutfitsTable extends CachedOutfits
    with TableInfo<$CachedOutfitsTable, CachedOutfit> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedOutfitsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      hasAutoIncrement: true,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('PRIMARY KEY AUTOINCREMENT'));
  static const VerificationMeta _briefMeta = const VerificationMeta('brief');
  @override
  late final GeneratedColumn<String> brief = GeneratedColumn<String>(
      'brief', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _imageBase64Meta =
      const VerificationMeta('imageBase64');
  @override
  late final GeneratedColumn<String> imageBase64 = GeneratedColumn<String>(
      'image_base64', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _promptMeta = const VerificationMeta('prompt');
  @override
  late final GeneratedColumn<String> prompt = GeneratedColumn<String>(
      'prompt', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _clipScoreMeta =
      const VerificationMeta('clipScore');
  @override
  late final GeneratedColumn<double> clipScore = GeneratedColumn<double>(
      'clip_score', aliasedName, false,
      type: DriftSqlType.double,
      requiredDuringInsert: false,
      defaultValue: const Constant(0.0));
  static const VerificationMeta _cachedAtMeta =
      const VerificationMeta('cachedAt');
  @override
  late final GeneratedColumn<DateTime> cachedAt = GeneratedColumn<DateTime>(
      'cached_at', aliasedName, false,
      type: DriftSqlType.dateTime,
      requiredDuringInsert: false,
      defaultValue: currentDateAndTime);
  @override
  List<GeneratedColumn> get $columns =>
      [id, brief, imageBase64, prompt, clipScore, cachedAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_outfits';
  @override
  VerificationContext validateIntegrity(Insertable<CachedOutfit> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('brief')) {
      context.handle(
          _briefMeta, brief.isAcceptableOrUnknown(data['brief']!, _briefMeta));
    } else if (isInserting) {
      context.missing(_briefMeta);
    }
    if (data.containsKey('image_base64')) {
      context.handle(
          _imageBase64Meta,
          imageBase64.isAcceptableOrUnknown(
              data['image_base64']!, _imageBase64Meta));
    }
    if (data.containsKey('prompt')) {
      context.handle(_promptMeta,
          prompt.isAcceptableOrUnknown(data['prompt']!, _promptMeta));
    }
    if (data.containsKey('clip_score')) {
      context.handle(_clipScoreMeta,
          clipScore.isAcceptableOrUnknown(data['clip_score']!, _clipScoreMeta));
    }
    if (data.containsKey('cached_at')) {
      context.handle(_cachedAtMeta,
          cachedAt.isAcceptableOrUnknown(data['cached_at']!, _cachedAtMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedOutfit map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedOutfit(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      brief: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}brief'])!,
      imageBase64: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}image_base64']),
      prompt: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}prompt']),
      clipScore: attachedDatabase.typeMapping
          .read(DriftSqlType.double, data['${effectivePrefix}clip_score'])!,
      cachedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}cached_at'])!,
    );
  }

  @override
  $CachedOutfitsTable createAlias(String alias) {
    return $CachedOutfitsTable(attachedDatabase, alias);
  }
}

class CachedOutfit extends DataClass implements Insertable<CachedOutfit> {
  final int id;
  final String brief;
  final String? imageBase64;
  final String? prompt;
  final double clipScore;
  final DateTime cachedAt;
  const CachedOutfit(
      {required this.id,
      required this.brief,
      this.imageBase64,
      this.prompt,
      required this.clipScore,
      required this.cachedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['brief'] = Variable<String>(brief);
    if (!nullToAbsent || imageBase64 != null) {
      map['image_base64'] = Variable<String>(imageBase64);
    }
    if (!nullToAbsent || prompt != null) {
      map['prompt'] = Variable<String>(prompt);
    }
    map['clip_score'] = Variable<double>(clipScore);
    map['cached_at'] = Variable<DateTime>(cachedAt);
    return map;
  }

  CachedOutfitsCompanion toCompanion(bool nullToAbsent) {
    return CachedOutfitsCompanion(
      id: Value(id),
      brief: Value(brief),
      imageBase64: imageBase64 == null && nullToAbsent
          ? const Value.absent()
          : Value(imageBase64),
      prompt:
          prompt == null && nullToAbsent ? const Value.absent() : Value(prompt),
      clipScore: Value(clipScore),
      cachedAt: Value(cachedAt),
    );
  }

  factory CachedOutfit.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedOutfit(
      id: serializer.fromJson<int>(json['id']),
      brief: serializer.fromJson<String>(json['brief']),
      imageBase64: serializer.fromJson<String?>(json['imageBase64']),
      prompt: serializer.fromJson<String?>(json['prompt']),
      clipScore: serializer.fromJson<double>(json['clipScore']),
      cachedAt: serializer.fromJson<DateTime>(json['cachedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'brief': serializer.toJson<String>(brief),
      'imageBase64': serializer.toJson<String?>(imageBase64),
      'prompt': serializer.toJson<String?>(prompt),
      'clipScore': serializer.toJson<double>(clipScore),
      'cachedAt': serializer.toJson<DateTime>(cachedAt),
    };
  }

  CachedOutfit copyWith(
          {int? id,
          String? brief,
          Value<String?> imageBase64 = const Value.absent(),
          Value<String?> prompt = const Value.absent(),
          double? clipScore,
          DateTime? cachedAt}) =>
      CachedOutfit(
        id: id ?? this.id,
        brief: brief ?? this.brief,
        imageBase64: imageBase64.present ? imageBase64.value : this.imageBase64,
        prompt: prompt.present ? prompt.value : this.prompt,
        clipScore: clipScore ?? this.clipScore,
        cachedAt: cachedAt ?? this.cachedAt,
      );
  CachedOutfit copyWithCompanion(CachedOutfitsCompanion data) {
    return CachedOutfit(
      id: data.id.present ? data.id.value : this.id,
      brief: data.brief.present ? data.brief.value : this.brief,
      imageBase64:
          data.imageBase64.present ? data.imageBase64.value : this.imageBase64,
      prompt: data.prompt.present ? data.prompt.value : this.prompt,
      clipScore: data.clipScore.present ? data.clipScore.value : this.clipScore,
      cachedAt: data.cachedAt.present ? data.cachedAt.value : this.cachedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedOutfit(')
          ..write('id: $id, ')
          ..write('brief: $brief, ')
          ..write('imageBase64: $imageBase64, ')
          ..write('prompt: $prompt, ')
          ..write('clipScore: $clipScore, ')
          ..write('cachedAt: $cachedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, brief, imageBase64, prompt, clipScore, cachedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedOutfit &&
          other.id == this.id &&
          other.brief == this.brief &&
          other.imageBase64 == this.imageBase64 &&
          other.prompt == this.prompt &&
          other.clipScore == this.clipScore &&
          other.cachedAt == this.cachedAt);
}

class CachedOutfitsCompanion extends UpdateCompanion<CachedOutfit> {
  final Value<int> id;
  final Value<String> brief;
  final Value<String?> imageBase64;
  final Value<String?> prompt;
  final Value<double> clipScore;
  final Value<DateTime> cachedAt;
  const CachedOutfitsCompanion({
    this.id = const Value.absent(),
    this.brief = const Value.absent(),
    this.imageBase64 = const Value.absent(),
    this.prompt = const Value.absent(),
    this.clipScore = const Value.absent(),
    this.cachedAt = const Value.absent(),
  });
  CachedOutfitsCompanion.insert({
    this.id = const Value.absent(),
    required String brief,
    this.imageBase64 = const Value.absent(),
    this.prompt = const Value.absent(),
    this.clipScore = const Value.absent(),
    this.cachedAt = const Value.absent(),
  }) : brief = Value(brief);
  static Insertable<CachedOutfit> custom({
    Expression<int>? id,
    Expression<String>? brief,
    Expression<String>? imageBase64,
    Expression<String>? prompt,
    Expression<double>? clipScore,
    Expression<DateTime>? cachedAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (brief != null) 'brief': brief,
      if (imageBase64 != null) 'image_base64': imageBase64,
      if (prompt != null) 'prompt': prompt,
      if (clipScore != null) 'clip_score': clipScore,
      if (cachedAt != null) 'cached_at': cachedAt,
    });
  }

  CachedOutfitsCompanion copyWith(
      {Value<int>? id,
      Value<String>? brief,
      Value<String?>? imageBase64,
      Value<String?>? prompt,
      Value<double>? clipScore,
      Value<DateTime>? cachedAt}) {
    return CachedOutfitsCompanion(
      id: id ?? this.id,
      brief: brief ?? this.brief,
      imageBase64: imageBase64 ?? this.imageBase64,
      prompt: prompt ?? this.prompt,
      clipScore: clipScore ?? this.clipScore,
      cachedAt: cachedAt ?? this.cachedAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (brief.present) {
      map['brief'] = Variable<String>(brief.value);
    }
    if (imageBase64.present) {
      map['image_base64'] = Variable<String>(imageBase64.value);
    }
    if (prompt.present) {
      map['prompt'] = Variable<String>(prompt.value);
    }
    if (clipScore.present) {
      map['clip_score'] = Variable<double>(clipScore.value);
    }
    if (cachedAt.present) {
      map['cached_at'] = Variable<DateTime>(cachedAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedOutfitsCompanion(')
          ..write('id: $id, ')
          ..write('brief: $brief, ')
          ..write('imageBase64: $imageBase64, ')
          ..write('prompt: $prompt, ')
          ..write('clipScore: $clipScore, ')
          ..write('cachedAt: $cachedAt')
          ..write(')'))
        .toString();
  }
}

class $CachedProductsTable extends CachedProducts
    with TableInfo<$CachedProductsTable, CachedProduct> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedProductsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _productIdMeta =
      const VerificationMeta('productId');
  @override
  late final GeneratedColumn<String> productId = GeneratedColumn<String>(
      'product_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
      'name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _priceInrMeta =
      const VerificationMeta('priceInr');
  @override
  late final GeneratedColumn<double> priceInr = GeneratedColumn<double>(
      'price_inr', aliasedName, false,
      type: DriftSqlType.double,
      requiredDuringInsert: false,
      defaultValue: const Constant(0));
  static const VerificationMeta _platformMeta =
      const VerificationMeta('platform');
  @override
  late final GeneratedColumn<String> platform = GeneratedColumn<String>(
      'platform', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _categoryMeta =
      const VerificationMeta('category');
  @override
  late final GeneratedColumn<String> category = GeneratedColumn<String>(
      'category', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _colorMeta = const VerificationMeta('color');
  @override
  late final GeneratedColumn<String> color = GeneratedColumn<String>(
      'color', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _affiliateUrlMeta =
      const VerificationMeta('affiliateUrl');
  @override
  late final GeneratedColumn<String> affiliateUrl = GeneratedColumn<String>(
      'affiliate_url', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _imageUrlMeta =
      const VerificationMeta('imageUrl');
  @override
  late final GeneratedColumn<String> imageUrl = GeneratedColumn<String>(
      'image_url', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _cachedAtMeta =
      const VerificationMeta('cachedAt');
  @override
  late final GeneratedColumn<DateTime> cachedAt = GeneratedColumn<DateTime>(
      'cached_at', aliasedName, false,
      type: DriftSqlType.dateTime,
      requiredDuringInsert: false,
      defaultValue: currentDateAndTime);
  @override
  List<GeneratedColumn> get $columns => [
        productId,
        name,
        priceInr,
        platform,
        category,
        color,
        affiliateUrl,
        imageUrl,
        cachedAt
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_products';
  @override
  VerificationContext validateIntegrity(Insertable<CachedProduct> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('product_id')) {
      context.handle(_productIdMeta,
          productId.isAcceptableOrUnknown(data['product_id']!, _productIdMeta));
    } else if (isInserting) {
      context.missing(_productIdMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
          _nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('price_inr')) {
      context.handle(_priceInrMeta,
          priceInr.isAcceptableOrUnknown(data['price_inr']!, _priceInrMeta));
    }
    if (data.containsKey('platform')) {
      context.handle(_platformMeta,
          platform.isAcceptableOrUnknown(data['platform']!, _platformMeta));
    }
    if (data.containsKey('category')) {
      context.handle(_categoryMeta,
          category.isAcceptableOrUnknown(data['category']!, _categoryMeta));
    }
    if (data.containsKey('color')) {
      context.handle(
          _colorMeta, color.isAcceptableOrUnknown(data['color']!, _colorMeta));
    }
    if (data.containsKey('affiliate_url')) {
      context.handle(
          _affiliateUrlMeta,
          affiliateUrl.isAcceptableOrUnknown(
              data['affiliate_url']!, _affiliateUrlMeta));
    }
    if (data.containsKey('image_url')) {
      context.handle(_imageUrlMeta,
          imageUrl.isAcceptableOrUnknown(data['image_url']!, _imageUrlMeta));
    }
    if (data.containsKey('cached_at')) {
      context.handle(_cachedAtMeta,
          cachedAt.isAcceptableOrUnknown(data['cached_at']!, _cachedAtMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {productId};
  @override
  CachedProduct map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedProduct(
      productId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}product_id'])!,
      name: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}name'])!,
      priceInr: attachedDatabase.typeMapping
          .read(DriftSqlType.double, data['${effectivePrefix}price_inr'])!,
      platform: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}platform']),
      category: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}category']),
      color: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}color']),
      affiliateUrl: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}affiliate_url']),
      imageUrl: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}image_url']),
      cachedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}cached_at'])!,
    );
  }

  @override
  $CachedProductsTable createAlias(String alias) {
    return $CachedProductsTable(attachedDatabase, alias);
  }
}

class CachedProduct extends DataClass implements Insertable<CachedProduct> {
  final String productId;
  final String name;
  final double priceInr;
  final String? platform;
  final String? category;
  final String? color;
  final String? affiliateUrl;
  final String? imageUrl;
  final DateTime cachedAt;
  const CachedProduct(
      {required this.productId,
      required this.name,
      required this.priceInr,
      this.platform,
      this.category,
      this.color,
      this.affiliateUrl,
      this.imageUrl,
      required this.cachedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['product_id'] = Variable<String>(productId);
    map['name'] = Variable<String>(name);
    map['price_inr'] = Variable<double>(priceInr);
    if (!nullToAbsent || platform != null) {
      map['platform'] = Variable<String>(platform);
    }
    if (!nullToAbsent || category != null) {
      map['category'] = Variable<String>(category);
    }
    if (!nullToAbsent || color != null) {
      map['color'] = Variable<String>(color);
    }
    if (!nullToAbsent || affiliateUrl != null) {
      map['affiliate_url'] = Variable<String>(affiliateUrl);
    }
    if (!nullToAbsent || imageUrl != null) {
      map['image_url'] = Variable<String>(imageUrl);
    }
    map['cached_at'] = Variable<DateTime>(cachedAt);
    return map;
  }

  CachedProductsCompanion toCompanion(bool nullToAbsent) {
    return CachedProductsCompanion(
      productId: Value(productId),
      name: Value(name),
      priceInr: Value(priceInr),
      platform: platform == null && nullToAbsent
          ? const Value.absent()
          : Value(platform),
      category: category == null && nullToAbsent
          ? const Value.absent()
          : Value(category),
      color:
          color == null && nullToAbsent ? const Value.absent() : Value(color),
      affiliateUrl: affiliateUrl == null && nullToAbsent
          ? const Value.absent()
          : Value(affiliateUrl),
      imageUrl: imageUrl == null && nullToAbsent
          ? const Value.absent()
          : Value(imageUrl),
      cachedAt: Value(cachedAt),
    );
  }

  factory CachedProduct.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedProduct(
      productId: serializer.fromJson<String>(json['productId']),
      name: serializer.fromJson<String>(json['name']),
      priceInr: serializer.fromJson<double>(json['priceInr']),
      platform: serializer.fromJson<String?>(json['platform']),
      category: serializer.fromJson<String?>(json['category']),
      color: serializer.fromJson<String?>(json['color']),
      affiliateUrl: serializer.fromJson<String?>(json['affiliateUrl']),
      imageUrl: serializer.fromJson<String?>(json['imageUrl']),
      cachedAt: serializer.fromJson<DateTime>(json['cachedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'productId': serializer.toJson<String>(productId),
      'name': serializer.toJson<String>(name),
      'priceInr': serializer.toJson<double>(priceInr),
      'platform': serializer.toJson<String?>(platform),
      'category': serializer.toJson<String?>(category),
      'color': serializer.toJson<String?>(color),
      'affiliateUrl': serializer.toJson<String?>(affiliateUrl),
      'imageUrl': serializer.toJson<String?>(imageUrl),
      'cachedAt': serializer.toJson<DateTime>(cachedAt),
    };
  }

  CachedProduct copyWith(
          {String? productId,
          String? name,
          double? priceInr,
          Value<String?> platform = const Value.absent(),
          Value<String?> category = const Value.absent(),
          Value<String?> color = const Value.absent(),
          Value<String?> affiliateUrl = const Value.absent(),
          Value<String?> imageUrl = const Value.absent(),
          DateTime? cachedAt}) =>
      CachedProduct(
        productId: productId ?? this.productId,
        name: name ?? this.name,
        priceInr: priceInr ?? this.priceInr,
        platform: platform.present ? platform.value : this.platform,
        category: category.present ? category.value : this.category,
        color: color.present ? color.value : this.color,
        affiliateUrl:
            affiliateUrl.present ? affiliateUrl.value : this.affiliateUrl,
        imageUrl: imageUrl.present ? imageUrl.value : this.imageUrl,
        cachedAt: cachedAt ?? this.cachedAt,
      );
  CachedProduct copyWithCompanion(CachedProductsCompanion data) {
    return CachedProduct(
      productId: data.productId.present ? data.productId.value : this.productId,
      name: data.name.present ? data.name.value : this.name,
      priceInr: data.priceInr.present ? data.priceInr.value : this.priceInr,
      platform: data.platform.present ? data.platform.value : this.platform,
      category: data.category.present ? data.category.value : this.category,
      color: data.color.present ? data.color.value : this.color,
      affiliateUrl: data.affiliateUrl.present
          ? data.affiliateUrl.value
          : this.affiliateUrl,
      imageUrl: data.imageUrl.present ? data.imageUrl.value : this.imageUrl,
      cachedAt: data.cachedAt.present ? data.cachedAt.value : this.cachedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedProduct(')
          ..write('productId: $productId, ')
          ..write('name: $name, ')
          ..write('priceInr: $priceInr, ')
          ..write('platform: $platform, ')
          ..write('category: $category, ')
          ..write('color: $color, ')
          ..write('affiliateUrl: $affiliateUrl, ')
          ..write('imageUrl: $imageUrl, ')
          ..write('cachedAt: $cachedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(productId, name, priceInr, platform, category,
      color, affiliateUrl, imageUrl, cachedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedProduct &&
          other.productId == this.productId &&
          other.name == this.name &&
          other.priceInr == this.priceInr &&
          other.platform == this.platform &&
          other.category == this.category &&
          other.color == this.color &&
          other.affiliateUrl == this.affiliateUrl &&
          other.imageUrl == this.imageUrl &&
          other.cachedAt == this.cachedAt);
}

class CachedProductsCompanion extends UpdateCompanion<CachedProduct> {
  final Value<String> productId;
  final Value<String> name;
  final Value<double> priceInr;
  final Value<String?> platform;
  final Value<String?> category;
  final Value<String?> color;
  final Value<String?> affiliateUrl;
  final Value<String?> imageUrl;
  final Value<DateTime> cachedAt;
  final Value<int> rowid;
  const CachedProductsCompanion({
    this.productId = const Value.absent(),
    this.name = const Value.absent(),
    this.priceInr = const Value.absent(),
    this.platform = const Value.absent(),
    this.category = const Value.absent(),
    this.color = const Value.absent(),
    this.affiliateUrl = const Value.absent(),
    this.imageUrl = const Value.absent(),
    this.cachedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedProductsCompanion.insert({
    required String productId,
    required String name,
    this.priceInr = const Value.absent(),
    this.platform = const Value.absent(),
    this.category = const Value.absent(),
    this.color = const Value.absent(),
    this.affiliateUrl = const Value.absent(),
    this.imageUrl = const Value.absent(),
    this.cachedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : productId = Value(productId),
        name = Value(name);
  static Insertable<CachedProduct> custom({
    Expression<String>? productId,
    Expression<String>? name,
    Expression<double>? priceInr,
    Expression<String>? platform,
    Expression<String>? category,
    Expression<String>? color,
    Expression<String>? affiliateUrl,
    Expression<String>? imageUrl,
    Expression<DateTime>? cachedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (productId != null) 'product_id': productId,
      if (name != null) 'name': name,
      if (priceInr != null) 'price_inr': priceInr,
      if (platform != null) 'platform': platform,
      if (category != null) 'category': category,
      if (color != null) 'color': color,
      if (affiliateUrl != null) 'affiliate_url': affiliateUrl,
      if (imageUrl != null) 'image_url': imageUrl,
      if (cachedAt != null) 'cached_at': cachedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedProductsCompanion copyWith(
      {Value<String>? productId,
      Value<String>? name,
      Value<double>? priceInr,
      Value<String?>? platform,
      Value<String?>? category,
      Value<String?>? color,
      Value<String?>? affiliateUrl,
      Value<String?>? imageUrl,
      Value<DateTime>? cachedAt,
      Value<int>? rowid}) {
    return CachedProductsCompanion(
      productId: productId ?? this.productId,
      name: name ?? this.name,
      priceInr: priceInr ?? this.priceInr,
      platform: platform ?? this.platform,
      category: category ?? this.category,
      color: color ?? this.color,
      affiliateUrl: affiliateUrl ?? this.affiliateUrl,
      imageUrl: imageUrl ?? this.imageUrl,
      cachedAt: cachedAt ?? this.cachedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (productId.present) {
      map['product_id'] = Variable<String>(productId.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (priceInr.present) {
      map['price_inr'] = Variable<double>(priceInr.value);
    }
    if (platform.present) {
      map['platform'] = Variable<String>(platform.value);
    }
    if (category.present) {
      map['category'] = Variable<String>(category.value);
    }
    if (color.present) {
      map['color'] = Variable<String>(color.value);
    }
    if (affiliateUrl.present) {
      map['affiliate_url'] = Variable<String>(affiliateUrl.value);
    }
    if (imageUrl.present) {
      map['image_url'] = Variable<String>(imageUrl.value);
    }
    if (cachedAt.present) {
      map['cached_at'] = Variable<DateTime>(cachedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedProductsCompanion(')
          ..write('productId: $productId, ')
          ..write('name: $name, ')
          ..write('priceInr: $priceInr, ')
          ..write('platform: $platform, ')
          ..write('category: $category, ')
          ..write('color: $color, ')
          ..write('affiliateUrl: $affiliateUrl, ')
          ..write('imageUrl: $imageUrl, ')
          ..write('cachedAt: $cachedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SyncQueueTable extends SyncQueue
    with TableInfo<$SyncQueueTable, SyncQueueData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncQueueTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      hasAutoIncrement: true,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('PRIMARY KEY AUTOINCREMENT'));
  static const VerificationMeta _actionMeta = const VerificationMeta('action');
  @override
  late final GeneratedColumn<String> action = GeneratedColumn<String>(
      'action', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _payloadJsonMeta =
      const VerificationMeta('payloadJson');
  @override
  late final GeneratedColumn<String> payloadJson = GeneratedColumn<String>(
      'payload_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _createdAtMeta =
      const VerificationMeta('createdAt');
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
      'created_at', aliasedName, false,
      type: DriftSqlType.dateTime,
      requiredDuringInsert: false,
      defaultValue: currentDateAndTime);
  static const VerificationMeta _syncedMeta = const VerificationMeta('synced');
  @override
  late final GeneratedColumn<bool> synced = GeneratedColumn<bool>(
      'synced', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("synced" IN (0, 1))'),
      defaultValue: const Constant(false));
  @override
  List<GeneratedColumn> get $columns =>
      [id, action, payloadJson, createdAt, synced];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sync_queue';
  @override
  VerificationContext validateIntegrity(Insertable<SyncQueueData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('action')) {
      context.handle(_actionMeta,
          action.isAcceptableOrUnknown(data['action']!, _actionMeta));
    } else if (isInserting) {
      context.missing(_actionMeta);
    }
    if (data.containsKey('payload_json')) {
      context.handle(
          _payloadJsonMeta,
          payloadJson.isAcceptableOrUnknown(
              data['payload_json']!, _payloadJsonMeta));
    } else if (isInserting) {
      context.missing(_payloadJsonMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(_createdAtMeta,
          createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta));
    }
    if (data.containsKey('synced')) {
      context.handle(_syncedMeta,
          synced.isAcceptableOrUnknown(data['synced']!, _syncedMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  SyncQueueData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SyncQueueData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      action: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}action'])!,
      payloadJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}payload_json'])!,
      createdAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}created_at'])!,
      synced: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}synced'])!,
    );
  }

  @override
  $SyncQueueTable createAlias(String alias) {
    return $SyncQueueTable(attachedDatabase, alias);
  }
}

class SyncQueueData extends DataClass implements Insertable<SyncQueueData> {
  final int id;
  final String action;
  final String payloadJson;
  final DateTime createdAt;
  final bool synced;
  const SyncQueueData(
      {required this.id,
      required this.action,
      required this.payloadJson,
      required this.createdAt,
      required this.synced});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['action'] = Variable<String>(action);
    map['payload_json'] = Variable<String>(payloadJson);
    map['created_at'] = Variable<DateTime>(createdAt);
    map['synced'] = Variable<bool>(synced);
    return map;
  }

  SyncQueueCompanion toCompanion(bool nullToAbsent) {
    return SyncQueueCompanion(
      id: Value(id),
      action: Value(action),
      payloadJson: Value(payloadJson),
      createdAt: Value(createdAt),
      synced: Value(synced),
    );
  }

  factory SyncQueueData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SyncQueueData(
      id: serializer.fromJson<int>(json['id']),
      action: serializer.fromJson<String>(json['action']),
      payloadJson: serializer.fromJson<String>(json['payloadJson']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      synced: serializer.fromJson<bool>(json['synced']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'action': serializer.toJson<String>(action),
      'payloadJson': serializer.toJson<String>(payloadJson),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'synced': serializer.toJson<bool>(synced),
    };
  }

  SyncQueueData copyWith(
          {int? id,
          String? action,
          String? payloadJson,
          DateTime? createdAt,
          bool? synced}) =>
      SyncQueueData(
        id: id ?? this.id,
        action: action ?? this.action,
        payloadJson: payloadJson ?? this.payloadJson,
        createdAt: createdAt ?? this.createdAt,
        synced: synced ?? this.synced,
      );
  SyncQueueData copyWithCompanion(SyncQueueCompanion data) {
    return SyncQueueData(
      id: data.id.present ? data.id.value : this.id,
      action: data.action.present ? data.action.value : this.action,
      payloadJson:
          data.payloadJson.present ? data.payloadJson.value : this.payloadJson,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      synced: data.synced.present ? data.synced.value : this.synced,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SyncQueueData(')
          ..write('id: $id, ')
          ..write('action: $action, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('createdAt: $createdAt, ')
          ..write('synced: $synced')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, action, payloadJson, createdAt, synced);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncQueueData &&
          other.id == this.id &&
          other.action == this.action &&
          other.payloadJson == this.payloadJson &&
          other.createdAt == this.createdAt &&
          other.synced == this.synced);
}

class SyncQueueCompanion extends UpdateCompanion<SyncQueueData> {
  final Value<int> id;
  final Value<String> action;
  final Value<String> payloadJson;
  final Value<DateTime> createdAt;
  final Value<bool> synced;
  const SyncQueueCompanion({
    this.id = const Value.absent(),
    this.action = const Value.absent(),
    this.payloadJson = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.synced = const Value.absent(),
  });
  SyncQueueCompanion.insert({
    this.id = const Value.absent(),
    required String action,
    required String payloadJson,
    this.createdAt = const Value.absent(),
    this.synced = const Value.absent(),
  })  : action = Value(action),
        payloadJson = Value(payloadJson);
  static Insertable<SyncQueueData> custom({
    Expression<int>? id,
    Expression<String>? action,
    Expression<String>? payloadJson,
    Expression<DateTime>? createdAt,
    Expression<bool>? synced,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (action != null) 'action': action,
      if (payloadJson != null) 'payload_json': payloadJson,
      if (createdAt != null) 'created_at': createdAt,
      if (synced != null) 'synced': synced,
    });
  }

  SyncQueueCompanion copyWith(
      {Value<int>? id,
      Value<String>? action,
      Value<String>? payloadJson,
      Value<DateTime>? createdAt,
      Value<bool>? synced}) {
    return SyncQueueCompanion(
      id: id ?? this.id,
      action: action ?? this.action,
      payloadJson: payloadJson ?? this.payloadJson,
      createdAt: createdAt ?? this.createdAt,
      synced: synced ?? this.synced,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (action.present) {
      map['action'] = Variable<String>(action.value);
    }
    if (payloadJson.present) {
      map['payload_json'] = Variable<String>(payloadJson.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (synced.present) {
      map['synced'] = Variable<bool>(synced.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SyncQueueCompanion(')
          ..write('id: $id, ')
          ..write('action: $action, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('createdAt: $createdAt, ')
          ..write('synced: $synced')
          ..write(')'))
        .toString();
  }
}

class $UserPrefsTable extends UserPrefs
    with TableInfo<$UserPrefsTable, UserPref> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $UserPrefsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _keyMeta = const VerificationMeta('key');
  @override
  late final GeneratedColumn<String> key = GeneratedColumn<String>(
      'key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _valueMeta = const VerificationMeta('value');
  @override
  late final GeneratedColumn<String> value = GeneratedColumn<String>(
      'value', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [key, value];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'user_prefs';
  @override
  VerificationContext validateIntegrity(Insertable<UserPref> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('key')) {
      context.handle(
          _keyMeta, key.isAcceptableOrUnknown(data['key']!, _keyMeta));
    } else if (isInserting) {
      context.missing(_keyMeta);
    }
    if (data.containsKey('value')) {
      context.handle(
          _valueMeta, value.isAcceptableOrUnknown(data['value']!, _valueMeta));
    } else if (isInserting) {
      context.missing(_valueMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {key};
  @override
  UserPref map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return UserPref(
      key: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}key'])!,
      value: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}value'])!,
    );
  }

  @override
  $UserPrefsTable createAlias(String alias) {
    return $UserPrefsTable(attachedDatabase, alias);
  }
}

class UserPref extends DataClass implements Insertable<UserPref> {
  final String key;
  final String value;
  const UserPref({required this.key, required this.value});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['key'] = Variable<String>(key);
    map['value'] = Variable<String>(value);
    return map;
  }

  UserPrefsCompanion toCompanion(bool nullToAbsent) {
    return UserPrefsCompanion(
      key: Value(key),
      value: Value(value),
    );
  }

  factory UserPref.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return UserPref(
      key: serializer.fromJson<String>(json['key']),
      value: serializer.fromJson<String>(json['value']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'key': serializer.toJson<String>(key),
      'value': serializer.toJson<String>(value),
    };
  }

  UserPref copyWith({String? key, String? value}) => UserPref(
        key: key ?? this.key,
        value: value ?? this.value,
      );
  UserPref copyWithCompanion(UserPrefsCompanion data) {
    return UserPref(
      key: data.key.present ? data.key.value : this.key,
      value: data.value.present ? data.value.value : this.value,
    );
  }

  @override
  String toString() {
    return (StringBuffer('UserPref(')
          ..write('key: $key, ')
          ..write('value: $value')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(key, value);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is UserPref && other.key == this.key && other.value == this.value);
}

class UserPrefsCompanion extends UpdateCompanion<UserPref> {
  final Value<String> key;
  final Value<String> value;
  final Value<int> rowid;
  const UserPrefsCompanion({
    this.key = const Value.absent(),
    this.value = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  UserPrefsCompanion.insert({
    required String key,
    required String value,
    this.rowid = const Value.absent(),
  })  : key = Value(key),
        value = Value(value);
  static Insertable<UserPref> custom({
    Expression<String>? key,
    Expression<String>? value,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (key != null) 'key': key,
      if (value != null) 'value': value,
      if (rowid != null) 'rowid': rowid,
    });
  }

  UserPrefsCompanion copyWith(
      {Value<String>? key, Value<String>? value, Value<int>? rowid}) {
    return UserPrefsCompanion(
      key: key ?? this.key,
      value: value ?? this.value,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (key.present) {
      map['key'] = Variable<String>(key.value);
    }
    if (value.present) {
      map['value'] = Variable<String>(value.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('UserPrefsCompanion(')
          ..write('key: $key, ')
          ..write('value: $value, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $CachedOutfitsTable cachedOutfits = $CachedOutfitsTable(this);
  late final $CachedProductsTable cachedProducts = $CachedProductsTable(this);
  late final $SyncQueueTable syncQueue = $SyncQueueTable(this);
  late final $UserPrefsTable userPrefs = $UserPrefsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities =>
      [cachedOutfits, cachedProducts, syncQueue, userPrefs];
}

typedef $$CachedOutfitsTableCreateCompanionBuilder = CachedOutfitsCompanion
    Function({
  Value<int> id,
  required String brief,
  Value<String?> imageBase64,
  Value<String?> prompt,
  Value<double> clipScore,
  Value<DateTime> cachedAt,
});
typedef $$CachedOutfitsTableUpdateCompanionBuilder = CachedOutfitsCompanion
    Function({
  Value<int> id,
  Value<String> brief,
  Value<String?> imageBase64,
  Value<String?> prompt,
  Value<double> clipScore,
  Value<DateTime> cachedAt,
});

class $$CachedOutfitsTableFilterComposer
    extends Composer<_$AppDatabase, $CachedOutfitsTable> {
  $$CachedOutfitsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get brief => $composableBuilder(
      column: $table.brief, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get imageBase64 => $composableBuilder(
      column: $table.imageBase64, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get prompt => $composableBuilder(
      column: $table.prompt, builder: (column) => ColumnFilters(column));

  ColumnFilters<double> get clipScore => $composableBuilder(
      column: $table.clipScore, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get cachedAt => $composableBuilder(
      column: $table.cachedAt, builder: (column) => ColumnFilters(column));
}

class $$CachedOutfitsTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedOutfitsTable> {
  $$CachedOutfitsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get brief => $composableBuilder(
      column: $table.brief, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get imageBase64 => $composableBuilder(
      column: $table.imageBase64, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get prompt => $composableBuilder(
      column: $table.prompt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<double> get clipScore => $composableBuilder(
      column: $table.clipScore, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get cachedAt => $composableBuilder(
      column: $table.cachedAt, builder: (column) => ColumnOrderings(column));
}

class $$CachedOutfitsTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedOutfitsTable> {
  $$CachedOutfitsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get brief =>
      $composableBuilder(column: $table.brief, builder: (column) => column);

  GeneratedColumn<String> get imageBase64 => $composableBuilder(
      column: $table.imageBase64, builder: (column) => column);

  GeneratedColumn<String> get prompt =>
      $composableBuilder(column: $table.prompt, builder: (column) => column);

  GeneratedColumn<double> get clipScore =>
      $composableBuilder(column: $table.clipScore, builder: (column) => column);

  GeneratedColumn<DateTime> get cachedAt =>
      $composableBuilder(column: $table.cachedAt, builder: (column) => column);
}

class $$CachedOutfitsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $CachedOutfitsTable,
    CachedOutfit,
    $$CachedOutfitsTableFilterComposer,
    $$CachedOutfitsTableOrderingComposer,
    $$CachedOutfitsTableAnnotationComposer,
    $$CachedOutfitsTableCreateCompanionBuilder,
    $$CachedOutfitsTableUpdateCompanionBuilder,
    (
      CachedOutfit,
      BaseReferences<_$AppDatabase, $CachedOutfitsTable, CachedOutfit>
    ),
    CachedOutfit,
    PrefetchHooks Function()> {
  $$CachedOutfitsTableTableManager(_$AppDatabase db, $CachedOutfitsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedOutfitsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedOutfitsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedOutfitsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> brief = const Value.absent(),
            Value<String?> imageBase64 = const Value.absent(),
            Value<String?> prompt = const Value.absent(),
            Value<double> clipScore = const Value.absent(),
            Value<DateTime> cachedAt = const Value.absent(),
          }) =>
              CachedOutfitsCompanion(
            id: id,
            brief: brief,
            imageBase64: imageBase64,
            prompt: prompt,
            clipScore: clipScore,
            cachedAt: cachedAt,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            required String brief,
            Value<String?> imageBase64 = const Value.absent(),
            Value<String?> prompt = const Value.absent(),
            Value<double> clipScore = const Value.absent(),
            Value<DateTime> cachedAt = const Value.absent(),
          }) =>
              CachedOutfitsCompanion.insert(
            id: id,
            brief: brief,
            imageBase64: imageBase64,
            prompt: prompt,
            clipScore: clipScore,
            cachedAt: cachedAt,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedOutfitsTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $CachedOutfitsTable,
    CachedOutfit,
    $$CachedOutfitsTableFilterComposer,
    $$CachedOutfitsTableOrderingComposer,
    $$CachedOutfitsTableAnnotationComposer,
    $$CachedOutfitsTableCreateCompanionBuilder,
    $$CachedOutfitsTableUpdateCompanionBuilder,
    (
      CachedOutfit,
      BaseReferences<_$AppDatabase, $CachedOutfitsTable, CachedOutfit>
    ),
    CachedOutfit,
    PrefetchHooks Function()>;
typedef $$CachedProductsTableCreateCompanionBuilder = CachedProductsCompanion
    Function({
  required String productId,
  required String name,
  Value<double> priceInr,
  Value<String?> platform,
  Value<String?> category,
  Value<String?> color,
  Value<String?> affiliateUrl,
  Value<String?> imageUrl,
  Value<DateTime> cachedAt,
  Value<int> rowid,
});
typedef $$CachedProductsTableUpdateCompanionBuilder = CachedProductsCompanion
    Function({
  Value<String> productId,
  Value<String> name,
  Value<double> priceInr,
  Value<String?> platform,
  Value<String?> category,
  Value<String?> color,
  Value<String?> affiliateUrl,
  Value<String?> imageUrl,
  Value<DateTime> cachedAt,
  Value<int> rowid,
});

class $$CachedProductsTableFilterComposer
    extends Composer<_$AppDatabase, $CachedProductsTable> {
  $$CachedProductsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnFilters(column));

  ColumnFilters<double> get priceInr => $composableBuilder(
      column: $table.priceInr, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get platform => $composableBuilder(
      column: $table.platform, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get category => $composableBuilder(
      column: $table.category, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get color => $composableBuilder(
      column: $table.color, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get affiliateUrl => $composableBuilder(
      column: $table.affiliateUrl, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get imageUrl => $composableBuilder(
      column: $table.imageUrl, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get cachedAt => $composableBuilder(
      column: $table.cachedAt, builder: (column) => ColumnFilters(column));
}

class $$CachedProductsTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedProductsTable> {
  $$CachedProductsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get productId => $composableBuilder(
      column: $table.productId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<double> get priceInr => $composableBuilder(
      column: $table.priceInr, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get platform => $composableBuilder(
      column: $table.platform, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get category => $composableBuilder(
      column: $table.category, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get color => $composableBuilder(
      column: $table.color, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get affiliateUrl => $composableBuilder(
      column: $table.affiliateUrl,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get imageUrl => $composableBuilder(
      column: $table.imageUrl, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get cachedAt => $composableBuilder(
      column: $table.cachedAt, builder: (column) => ColumnOrderings(column));
}

class $$CachedProductsTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedProductsTable> {
  $$CachedProductsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get productId =>
      $composableBuilder(column: $table.productId, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<double> get priceInr =>
      $composableBuilder(column: $table.priceInr, builder: (column) => column);

  GeneratedColumn<String> get platform =>
      $composableBuilder(column: $table.platform, builder: (column) => column);

  GeneratedColumn<String> get category =>
      $composableBuilder(column: $table.category, builder: (column) => column);

  GeneratedColumn<String> get color =>
      $composableBuilder(column: $table.color, builder: (column) => column);

  GeneratedColumn<String> get affiliateUrl => $composableBuilder(
      column: $table.affiliateUrl, builder: (column) => column);

  GeneratedColumn<String> get imageUrl =>
      $composableBuilder(column: $table.imageUrl, builder: (column) => column);

  GeneratedColumn<DateTime> get cachedAt =>
      $composableBuilder(column: $table.cachedAt, builder: (column) => column);
}

class $$CachedProductsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $CachedProductsTable,
    CachedProduct,
    $$CachedProductsTableFilterComposer,
    $$CachedProductsTableOrderingComposer,
    $$CachedProductsTableAnnotationComposer,
    $$CachedProductsTableCreateCompanionBuilder,
    $$CachedProductsTableUpdateCompanionBuilder,
    (
      CachedProduct,
      BaseReferences<_$AppDatabase, $CachedProductsTable, CachedProduct>
    ),
    CachedProduct,
    PrefetchHooks Function()> {
  $$CachedProductsTableTableManager(
      _$AppDatabase db, $CachedProductsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedProductsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedProductsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedProductsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> productId = const Value.absent(),
            Value<String> name = const Value.absent(),
            Value<double> priceInr = const Value.absent(),
            Value<String?> platform = const Value.absent(),
            Value<String?> category = const Value.absent(),
            Value<String?> color = const Value.absent(),
            Value<String?> affiliateUrl = const Value.absent(),
            Value<String?> imageUrl = const Value.absent(),
            Value<DateTime> cachedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedProductsCompanion(
            productId: productId,
            name: name,
            priceInr: priceInr,
            platform: platform,
            category: category,
            color: color,
            affiliateUrl: affiliateUrl,
            imageUrl: imageUrl,
            cachedAt: cachedAt,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String productId,
            required String name,
            Value<double> priceInr = const Value.absent(),
            Value<String?> platform = const Value.absent(),
            Value<String?> category = const Value.absent(),
            Value<String?> color = const Value.absent(),
            Value<String?> affiliateUrl = const Value.absent(),
            Value<String?> imageUrl = const Value.absent(),
            Value<DateTime> cachedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedProductsCompanion.insert(
            productId: productId,
            name: name,
            priceInr: priceInr,
            platform: platform,
            category: category,
            color: color,
            affiliateUrl: affiliateUrl,
            imageUrl: imageUrl,
            cachedAt: cachedAt,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedProductsTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $CachedProductsTable,
    CachedProduct,
    $$CachedProductsTableFilterComposer,
    $$CachedProductsTableOrderingComposer,
    $$CachedProductsTableAnnotationComposer,
    $$CachedProductsTableCreateCompanionBuilder,
    $$CachedProductsTableUpdateCompanionBuilder,
    (
      CachedProduct,
      BaseReferences<_$AppDatabase, $CachedProductsTable, CachedProduct>
    ),
    CachedProduct,
    PrefetchHooks Function()>;
typedef $$SyncQueueTableCreateCompanionBuilder = SyncQueueCompanion Function({
  Value<int> id,
  required String action,
  required String payloadJson,
  Value<DateTime> createdAt,
  Value<bool> synced,
});
typedef $$SyncQueueTableUpdateCompanionBuilder = SyncQueueCompanion Function({
  Value<int> id,
  Value<String> action,
  Value<String> payloadJson,
  Value<DateTime> createdAt,
  Value<bool> synced,
});

class $$SyncQueueTableFilterComposer
    extends Composer<_$AppDatabase, $SyncQueueTable> {
  $$SyncQueueTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get action => $composableBuilder(
      column: $table.action, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get synced => $composableBuilder(
      column: $table.synced, builder: (column) => ColumnFilters(column));
}

class $$SyncQueueTableOrderingComposer
    extends Composer<_$AppDatabase, $SyncQueueTable> {
  $$SyncQueueTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get action => $composableBuilder(
      column: $table.action, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get synced => $composableBuilder(
      column: $table.synced, builder: (column) => ColumnOrderings(column));
}

class $$SyncQueueTableAnnotationComposer
    extends Composer<_$AppDatabase, $SyncQueueTable> {
  $$SyncQueueTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get action =>
      $composableBuilder(column: $table.action, builder: (column) => column);

  GeneratedColumn<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<bool> get synced =>
      $composableBuilder(column: $table.synced, builder: (column) => column);
}

class $$SyncQueueTableTableManager extends RootTableManager<
    _$AppDatabase,
    $SyncQueueTable,
    SyncQueueData,
    $$SyncQueueTableFilterComposer,
    $$SyncQueueTableOrderingComposer,
    $$SyncQueueTableAnnotationComposer,
    $$SyncQueueTableCreateCompanionBuilder,
    $$SyncQueueTableUpdateCompanionBuilder,
    (
      SyncQueueData,
      BaseReferences<_$AppDatabase, $SyncQueueTable, SyncQueueData>
    ),
    SyncQueueData,
    PrefetchHooks Function()> {
  $$SyncQueueTableTableManager(_$AppDatabase db, $SyncQueueTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SyncQueueTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SyncQueueTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SyncQueueTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> action = const Value.absent(),
            Value<String> payloadJson = const Value.absent(),
            Value<DateTime> createdAt = const Value.absent(),
            Value<bool> synced = const Value.absent(),
          }) =>
              SyncQueueCompanion(
            id: id,
            action: action,
            payloadJson: payloadJson,
            createdAt: createdAt,
            synced: synced,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            required String action,
            required String payloadJson,
            Value<DateTime> createdAt = const Value.absent(),
            Value<bool> synced = const Value.absent(),
          }) =>
              SyncQueueCompanion.insert(
            id: id,
            action: action,
            payloadJson: payloadJson,
            createdAt: createdAt,
            synced: synced,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$SyncQueueTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $SyncQueueTable,
    SyncQueueData,
    $$SyncQueueTableFilterComposer,
    $$SyncQueueTableOrderingComposer,
    $$SyncQueueTableAnnotationComposer,
    $$SyncQueueTableCreateCompanionBuilder,
    $$SyncQueueTableUpdateCompanionBuilder,
    (
      SyncQueueData,
      BaseReferences<_$AppDatabase, $SyncQueueTable, SyncQueueData>
    ),
    SyncQueueData,
    PrefetchHooks Function()>;
typedef $$UserPrefsTableCreateCompanionBuilder = UserPrefsCompanion Function({
  required String key,
  required String value,
  Value<int> rowid,
});
typedef $$UserPrefsTableUpdateCompanionBuilder = UserPrefsCompanion Function({
  Value<String> key,
  Value<String> value,
  Value<int> rowid,
});

class $$UserPrefsTableFilterComposer
    extends Composer<_$AppDatabase, $UserPrefsTable> {
  $$UserPrefsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get key => $composableBuilder(
      column: $table.key, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get value => $composableBuilder(
      column: $table.value, builder: (column) => ColumnFilters(column));
}

class $$UserPrefsTableOrderingComposer
    extends Composer<_$AppDatabase, $UserPrefsTable> {
  $$UserPrefsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get key => $composableBuilder(
      column: $table.key, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get value => $composableBuilder(
      column: $table.value, builder: (column) => ColumnOrderings(column));
}

class $$UserPrefsTableAnnotationComposer
    extends Composer<_$AppDatabase, $UserPrefsTable> {
  $$UserPrefsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get key =>
      $composableBuilder(column: $table.key, builder: (column) => column);

  GeneratedColumn<String> get value =>
      $composableBuilder(column: $table.value, builder: (column) => column);
}

class $$UserPrefsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $UserPrefsTable,
    UserPref,
    $$UserPrefsTableFilterComposer,
    $$UserPrefsTableOrderingComposer,
    $$UserPrefsTableAnnotationComposer,
    $$UserPrefsTableCreateCompanionBuilder,
    $$UserPrefsTableUpdateCompanionBuilder,
    (UserPref, BaseReferences<_$AppDatabase, $UserPrefsTable, UserPref>),
    UserPref,
    PrefetchHooks Function()> {
  $$UserPrefsTableTableManager(_$AppDatabase db, $UserPrefsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$UserPrefsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$UserPrefsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$UserPrefsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> key = const Value.absent(),
            Value<String> value = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              UserPrefsCompanion(
            key: key,
            value: value,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String key,
            required String value,
            Value<int> rowid = const Value.absent(),
          }) =>
              UserPrefsCompanion.insert(
            key: key,
            value: value,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$UserPrefsTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $UserPrefsTable,
    UserPref,
    $$UserPrefsTableFilterComposer,
    $$UserPrefsTableOrderingComposer,
    $$UserPrefsTableAnnotationComposer,
    $$UserPrefsTableCreateCompanionBuilder,
    $$UserPrefsTableUpdateCompanionBuilder,
    (UserPref, BaseReferences<_$AppDatabase, $UserPrefsTable, UserPref>),
    UserPref,
    PrefetchHooks Function()>;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$CachedOutfitsTableTableManager get cachedOutfits =>
      $$CachedOutfitsTableTableManager(_db, _db.cachedOutfits);
  $$CachedProductsTableTableManager get cachedProducts =>
      $$CachedProductsTableTableManager(_db, _db.cachedProducts);
  $$SyncQueueTableTableManager get syncQueue =>
      $$SyncQueueTableTableManager(_db, _db.syncQueue);
  $$UserPrefsTableTableManager get userPrefs =>
      $$UserPrefsTableTableManager(_db, _db.userPrefs);
}
