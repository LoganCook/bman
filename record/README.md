## Product management

Product in Dynamics has four types (`producttypecode`) and this property will
determine how the cost of an orderline is calculated:
1. Sales Inventory: usage is accumulated time. For example, job run hours.
1. Services: service usage is the maximal point usage and usage itself is not
   time related but billing period is. Storage is one example of service.
1. Flat Fees: fee is calculated by time used regardless of actual usage.
1. Miscellaneous Charges: fee is calculated by its accessories not by itself.
   The product is only a pseudo product.

| Product  | Type |
| ------------- | ------------- |
| HPC home storage | Flat Fees |
| Additonal VM Storage | Services |
| Attached Backup Storage | Services |
| Attached Storage | Services |
| Nectar Cloud VM | Flat Fees |
| TANGO Cloud VM | Miscellaneous Charges |
| TANGO VM CPU  - Not for sale | Services |
| TANGO VM Memory – Not for sale | Services |
| TANGO Compute | Sales Inventory |
| eRSA Account | Sales Inventory |

Product can have accessory products (defined as having substitutes by
`salesrelationshiptype = Accessory` in entity `productsubstitute`. In
eRSA CRM deployment, Accessory type substitute is reserved for composed
product in pricing.). If a product has accessories,
1: if it has type of `Miscellaneous Charges`, it is a pseudo product
   and the cost of an orderline of this product is done by the sum
   of all its accessories without itself;
2: if it has other types, the cost of an orderline of this product
   is done by the sum of the cost of this product and all its accessories.
So check productsubstitute table first: `api/product/substitute`.

The relation defined in CRM can be bypassed by not providing `substitutes-json`
when calling an ingest command.

## Record usages and fees in intervals

### Notes:
1. Prices in eRSA CRM are yearly rates: for example, one job runs for
   a year, one GB (storage or memory) consumed for a year or a CPU
   core used for a year.
1. For Fees or Usages, they are not events but statistics in intervals.
   So the queries run against [start, end] of an interval using equal at both ends.
1. Usage consists configuration of product and actual usage statistics. Usage
   data collected from `unified` API are split into two tables: configuration and usage.
1. Contract provides information for linking usage (including configuration) data and
   Contact and Account.
1. Depends on the product, the fields of contract (orderline) may be different.
1. In contracts (orderlines), special link property may missing if the
   properties of product have not been set, and there may be some extra
   properties are not needed for recording Fee or Usage.
1. To calculate fees, it always need configuration JSON file.
1. Root name of usage models and ingester classes should have only the first
   letter capitalized by convention.

```shell
python manage.py makemigrations record --settings=runner.record
# Want to view sql?
# python manage.py sqlmigrate record --settings runner.record 0001
python manage.py migrate --settings=runner.record

python manage.py test record.test_models --settings=runner.record

# should set initial date to 20160101 or other earlier date as a start date
python manage.py load_prices_products someurl/bman/api/pricelist/ -d 20160101 --settings=runner.record
# python manage.py ingest_contract -t tangovm --settings=runner.record
# python manage.py ingest_usage -c config_tango_simple.json -t tangovm -s 20180101 -e 20180131 --account-json ../ersa_accounts_20180501.json --contact-json ../ersa_contacts_20180605.json --settings=runner.record
# preferred and the only way for  getting nectar. the above commands are being deprecated
python manage.py ingest -c config_nectar.json -t nectarvm -s 20180101 -e 20180131 --account-json ../ersa_accounts_20180501.json --contact-json ../ersa_contacts_20180605.json --settings=runner.record
```
#### Command arguments:
1. fee/no-fee: ingest usage data and their contracts but do not calculate fees.
   This is useful when gathering usage data more frequently than billing.

```python
# make composed product:
from record.models import Product
products = Product.objects.all()
for product in products:
     print(product)

products[9].parent_id = products[1].pk
products[10].parent_id = products[1].pk
products[9].save()
products[10].save()
```

In configuration JSON file, `product-no` is VERY critical. Top level key is the class name of configuration model.
The class name of usage model is that name plus `Usage`. For example, if `Tangocloudvm`
is the `service-base-class-name`, the three classes should be:
`Tangocloudvm` and `TangocloudvmUsage` and `TangocloudvmIngester`. Ingester class should know which configuration and usage class.
```json
{
  "service-base-class-name": {
    "product-no": "32562",
    "CRM": {
      "url": "http://url/contract/somename/",
      "identifier": "field name to be used as identifier in Orderline"
    },
    "USAGE": {
      "original-data": {
        "url": "http://source-data-url",
        "headers": {
          "x-header-name": "some value"
        },
        "timeout": 10
      },
      "fields": {
        "orginal-field-name1": "map to field name",
        "orginal-field-name2": "map to field name"
      },
      "orderline": {
        "crm-linker": "field name holds the value to be used to link usage with contract",
        "aggregators":[
          "list",
          "of usage fields which will be used to create a composed identifier in orderline",
          "one example is queue in tizard"],
        "extra": {
          "orginal-field-name1": "map to field name",
          "orginal-field-name2": "map to field name",
          "orginal-field-name3": "map to field name",
        }
      },
      "composition": {
        "product number 1 from which price is from for": "field1",
        "product number 2 from which price is from for": "field2"
      }
    }
  }
}
```

When ingesting, linking Dynamics contract (orderline) and usage is done by
matching two identifer fields: `identifier` in `CRM` section and `crm-linker`
in `USAGE` section. Only __one__ field can be used to link CRM contracts to usage.
The `identifer` of table `Orderline` is not always created simply by saving
the value of `crm-linker` from a usage data object. Because `Orderline` is
the foreign key of `Fee`, if fee is grouped not only by the `identifer`
in Dynamics contract, it needs to be grouped by some other fields, then
they (`aggregators` in `USAGE->orderline`) have to be part of `identifer`
of table `Orderline`. This slightly breaks the definition of `Orderline`,
which is product based. This exemption is handled by code when calculating fees
in [frontend](https://github.com/eResearchSA/reporting-frontend/blob/master/js/services/slurm.js#L27).

If it is a composed product, you do not need to create relation in Product
table if no one is interested in it because fee calculation gets this relationship
from configuration JSON file. Fee calculation does not only need to know if a
product is a composed product and also which usage fields are used with each
of composed product for prices. Not all usage fields are used in fee calculation,
so normally fee cannot be calculated from the usage in database only without a
configuration JSON file.

Different service can have its own fields in `USAGE` section.

## __This paragraph and product_class_map.json need to be reviewed__
Product identifiers, e.g. name or product number, can be changed any time, but schema support products are not.
So we need to create a map reflects the implementation of the product catalogue in Dynamics. The map is defined in
`/product_class_map.json` at the base directory of the application. This file is referenced in `settings` of the
application. We choose product number as identifier. Each product number maps to the name of a configuration class.
The usage class can be obtained by adding `Usage` to the end of configuration class name. __If we force people use model class name, the the code can be linked to production by it number, there is no need for product_class_map.json.__

#### USAGE section in config.json
1. It information to get original data:
   1. source url;
   1. identifier for matching usage data to contract (order);
   1. optional headers for security.
1. `fields` represents a map between usage raw data and usage class.
1. `orderline` -> `crm-linker` links usage data to `Orderline` in database;
    and `orderline` -> `extra` represents an optional map between usage data
    and configuration class.
1. Composition section is for calculating fee if a product is a pseudo or super
   product. For some products, fee is calculated based on configuration, see
   code for details.
1. `fee-field`: if fee is calculated base on one value. _Normally, `fee-field`
   should be exclusive to `composition`_.

Base structure of contracts is common between orders
```JavaScript
  {
    "salesorderid": "604bfb44-8af9-e611-80e7-70106fa39b51",
    "managercontactid": "a2bd71c5-5b63-e611-80e3-c4346bc43f98",
    "manager": "Demo User",
    "managertitle": "Project Manager",
    "allocated": 11000,
    "unitPrice": 0.24,
    "salesorderdetail2_x002e_transactioncurrencyid": "744fd97c-18fb-e511-80d8-c4346bc5b718",
    "managerunit": "College of Humanities, Arts & Social Sciences",
    "pricelevelID@OData.Community.Display.V1.FormattedValue": "Members Price List",
    "manageremail": "demo.user@flinders.edu.au",
    "managercontactid@OData.Community.Display.V1.FormattedValue": "Demo User",
    "@odata.etag": "W/\"10232763\"",
    "allocated@OData.Community.Display.V1.FormattedValue": "11000",
    "unitPrice@OData.Community.Display.V1.FormattedValue": "$0.24",
    "orderID": "FUSA0003",
    "pricelevelID": "0c407dd9-1b59-e611-80e2-c4346bc58784",
    "name": "National Institute of Dramatic Art (NIDA) : Production Archives",
    "salesorderdetail2_x002e_transactioncurrencyid@OData.Community.Display.V1.FormattedValue": "Australian Dollar",
    "biller": "Flinders University"
  }
```

attachedstorage
```JavaScript
  {
    "salesorderid": "604bfb44-8af9-e611-80e7-70106fa39b51",
    "managercontactid": "a2bd71c5-5b63-e611-80e3-c4346bc43f98",
    "manager": "Demo User",
    "managertitle": "Project Manager",
    "allocated": 11000,
    "unitPrice": 0.24,
    "salesorderdetail2_x002e_transactioncurrencyid": "744fd97c-18fb-e511-80d8-c4346bc5b718",
    "managerunit": "College of Humanities, Arts & Social Sciences",
    "pricelevelID@OData.Community.Display.V1.FormattedValue": "Members Price List",
    "manageremail": "demo.user@flinders.edu.au",
    "managercontactid@OData.Community.Display.V1.FormattedValue": "Demo User",
    "@odata.etag": "W/\"10232763\"",
    "FileSystemName": "/export/compellent/ersa-fusa-nida-productionarchive-fusa0003",
    "GrantID": "http://purl.org/au-research/grants/arc/LE100100028",
    "allocated@OData.Community.Display.V1.FormattedValue": "11000",
    "unitPrice@OData.Community.Display.V1.FormattedValue": "$0.24",
    "orderID": "FUSA0003",
    "pricelevelID": "0c407dd9-1b59-e611-80e2-c4346bc58784",
    "name": "National Institute of Dramatic Art (NIDA) : Production Archives",
    "salesorderdetail2_x002e_transactioncurrencyid@OData.Community.Display.V1.FormattedValue": "Australian Dollar",
    "biller": "Flinders University"
  }
```

tangocloudvm
```JavaScript
[
  {
  "salesorderid": "ecdd3ac2-c0a8-e711-8130-70106fa3d971",
  "managercontactid": "e2e922c6-170a-e711-80eb-70106fa39b51",
  "manager": "Demo User",
  "managertitle": "Research Associate",
  "allocated": 16,
  "unitPrice": 240,
  "managerunit": "School of Biological Sciences",
  "pricelevelID@OData.Community.Display.V1.FormattedValue": "Members Price List",
  "manageremail": "demo.user@adelaide.edu.au",
  "managercontactid@OData.Community.Display.V1.FormattedValue": "Demo User",
  "@odata.etag": "W/\"9067537\"",
  "OpenstackProjectID": "vm-2135",
  "biller": "University of Adelaide",
  "salesorderdetail2_x002e_transactioncurrencyid": "744fd97c-18fb-e511-80d8-c4346bc5b718",
  "allocated@OData.Community.Display.V1.FormattedValue": "16",
  "unitPrice@OData.Community.Display.V1.FormattedValue": "$240.00",
  "orderID": "UOFA0138",
  "name": "Adelaide Global Ecology CED Tango VMs",
  "salesorderdetail2_x002e_transactioncurrencyid@OData.Community.Display.V1.FormattedValue": "Australian Dollar",
  "pricelevelID": "0c407dd9-1b59-e611-80e2-c4346bc58784"
}
  {
    "salesorderid": "a04bfb44-8af9-e611-80e7-70106fa39b51",
    "managercontactid": "38dbdc92-a999-e611-80eb-c4346bc4beac",
    "manager": "Demo User",
    "managertitle": "Research Scientist",
    "allocated": 12,
    "unitPrice": 240,
    "managerunit": "School of Biological Sciences",
    "pricelevelID@OData.Community.Display.V1.FormattedValue": "Members Price List",
    "manageremail": "demo.user@adelaide.edu.au",
    "managercontactid@OData.Community.Display.V1.FormattedValue": "Demo User",
    "@odata.etag": "W/\"11123313\"",
    "biller": "University of Adelaide",
    "salesorderdetail2_x002e_transactioncurrencyid": "744fd97c-18fb-e511-80d8-c4346bc5b718",
    "allocated@OData.Community.Display.V1.FormattedValue": "12",
    "unitPrice@OData.Community.Display.V1.FormattedValue": "$240.00",
    "orderID": "Cloud Demo User",
    "name": "Evolutionary Genomics Cloud Services",
    "salesorderdetail2_x002e_transactioncurrencyid@OData.Community.Display.V1.FormattedValue": "Australian Dollar",
    "pricelevelID": "0c407dd9-1b59-e611-80e2-c4346bc58784"
  },
  {
    "salesorderid": "a04bfb44-8af9-e611-80e7-70106fa39b51",
    "managercontactid": "38dbdc92-a999-e611-80eb-c4346bc4beac",
    "manager": "Demo User",
    "managertitle": "Research Scientist",
    "allocated": 12,
    "unitPrice": 240,
    "managerunit": "School of Biological Sciences",
    "pricelevelID@OData.Community.Display.V1.FormattedValue": "Members Price List",
    "manageremail": "demo.user@adelaide.edu.au",
    "managercontactid@OData.Community.Display.V1.FormattedValue": "Demo User",
    "@odata.etag": "W/\"11123313\"",
    "biller": "University of Adelaide",
    "salesorderdetail2_x002e_transactioncurrencyid": "744fd97c-18fb-e511-80d8-c4346bc5b718",
    "allocated@OData.Community.Display.V1.FormattedValue": "12",
    "unitPrice@OData.Community.Display.V1.FormattedValue": "$240.00",
    "orderID": "Cloud Demo User",
    "name": "Evolutionary Genomics Cloud Services",
    "salesorderdetail2_x002e_transactioncurrencyid@OData.Community.Display.V1.FormattedValue": "Australian Dollar",
    "pricelevelID": "0c407dd9-1b59-e611-80e2-c4346bc58784"
  }
]
```

Service targeted usage tables.
minimal item information:
    HPC: only job id, owner, run time (end-start), core used
        select owner_id, sum(job.end-start), sum(cores) as cores, sum(cpu_seconds) as cpu_seconds from job group by owner_id;
    nectar: instance_id, cpu, ram, disk, ephemeral
    xfs: filesystem, usage, soft, hard quota
    hcp: namespace, object count, in/out in bytes, in/out objects

Nectar and HPC are event based. Storages are snapshot based.

Event based usage: we can have an event (history) table:
start | end | id | details

Usage queries collect the events which have start and end time overlap with query time range.
Select * from event WHERE start <= query_start or end >= query_end

1. duration = end – start when start >= query_start and end <= query_end
2. duration = query_end – start when start > query_start and start < query_end and end > query_end
3. duration = end - query_start when start < query_start and end > query_start and end < query_end

Event based usage is the accumulated items.

Snapshot based: we have to collect all snapshots in the query range. Timestamps of snapshots have to be non-overlap. Resolution can be variable.
The usage is the avages of items

Service calculator:
1. constructor sets time interval of the calculation
2. get_data to retrieves raw data or ask database to do calculation
3. calculate usage:
   -. average usage
   -. accumulate events: running time -> instance (VM) with its resource (flavor)
                                      -> job (HPC) with its resource (core and cpu_seconds)
4. get owner or manager or account with depends on which service:
      -. manager: nectar instance
      -. contractor: storage
      -. account: HPC
    -. extend owner information to school and university
5. save to a file in json format

To decouple usage database, user links are regenerated because BMan is not
guaranteed to be used. Do the same trick used in load_csv of bman. This
is mainly for queries involve grouping by university, school. Also possible
to find heavy users.

quota (allocation) information may also need to ported over because they
are saved in BMan too.

When loading, make sure not interval overlapps with each other but can have gaps.
service and usage are both maps: defined by a particular service.
Each map listed here is a row in a database table.
{ organisation: ""
  school: "any second level of organisation",
  contactor: "name",
  email: "email",
  service: {
    id:xxx,
    name: xxx,
    queue: gx,
    username: someone,
  },
  usage: {
      cpu: 10,
      cpu_seconds: 100,
      duration: 100
  }
}

{ organisation: ""
  school: "any second level of organisation",
  contactor: "name",
  email: "email",
  service: {
    host: somehost
  }
  usage: {
      disk: 10,
      epheriaephemeral: 100,
      ram: 1,
      cpu: 4,
      duration: 100
  }
}

# xfs, hnas.filesystem and hnas.virtual-volume have usage field
{ organisation: ""
  school: "any second level of organisation",
  contactor: "name",
  email: "email",
  service: {
      filesystem:ss,
  }
  usage: {
      host: 'pl-cml-nss-01.blue.ersa.edu.au',
      filesystem: '/export/compellent/hpctest',
      soft: 10,
      hard: 10,
      usage: 0,
      owner: 'sj'
  }
}

# HCP has a usage table
{ organisation: ""
  school: "any second level of organisation",
  contactor: "name",
  email: "email",
  service: {
      namespace:ss,
  }
  usage: {
      objects: 10,
      ingested_bytes: 1,
      raw_bytes: 1,
      in_bytes: 1,
      out_bytes: 1,
      reads: 1,
      writes: 1,
      deletes: 1
  }
}

http://unified/hnas/filesystem/usage/summary?end=1517405400&start=1514727000

    {
        "live_usage": 755340,
        "filesystem": "ersa-vmware-backup",
        "capacity": 5920000,
        "snapshot_usage": 550250,
        "free": 5164660
    },

    'filesystem', 'capacity', 'free', 'live_usage', 'snapshot_usage'
entry['live_usage']/ 1000; MB to GB

http://unified/hnas/virtual-volume/usage/summary?end=1517405400&start=1514727000
    {
        "filesystem": "unisa",
        "owner": "",
        "usage": 0,
        "files": 2,
        "virtual_volume": "ITEE",
        "quota": 20480
    },
'filesystem', 'virtual_volume', 'owner', 'quota', 'files', 'usage'
 entry['usage'] / 1000; MB to GB

http://unified/xfs/usage/summary?end=1517405400&start=1514727000
    {
        "hard": 0,
        "usage": 0,
        "soft": 0,
        "filesystem": "/export/compellent/ersa-backups",
        "host": "pl-cml-nss-02.blue.ersa.edu.au"
    }
'host', 'filesystem', 'soft', 'hard', 'usage'
raw = entry['usage'] * 1024; KB -> B

http://unified/hcp/usage/summary?end=1517405400&start=1514727000
    {
        "ingested_bytes": 0,
        "bytes_in": 0,
        "namespace": "ersa-uofa-mbs-proteomics-35",
        "reads": 130,
        "writes": 0,
        "raw_bytes": 0,
        "metadata_only_bytes": 0,
        "metadata_only_objects": 0,
        "deletes": 0,
        "tiered_objects": 0,
        "bytes_out": 78260,
        "objects": 0,
        "tiered_bytes": 0
    },
'namespace', 'ingested_bytes', 'raw_bytes', 'reads',
                  'writes', 'deletes', 'objects', 'bytes_in', 'bytes_out',
                  'metadata_only_objects', 'metadata_only_bytes',
                  'tiered_objects', 'tiered_bytes'

ingested_bytes

Tests:
1. only recognised service can be processed, any other string will fail
2. can generate json file
3. json in the file is an array of json
4. each json has at least organisation, school, contactor, email, service and usage fields
