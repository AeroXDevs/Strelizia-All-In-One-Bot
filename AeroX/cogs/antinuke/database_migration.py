
import aiosqlite 
import asyncio 

async def migrate_whitelist_table ():
    """Migrate whitelist table to include all necessary columns"""
    try :
        async with aiosqlite .connect ('db/anti.db')as db :

            cursor =await db .execute ("PRAGMA table_info(whitelisted_users)")
            existing_columns =[row [1 ]for row in await cursor .fetchall ()]


            columns_to_add =[
            ('rlcr','BOOLEAN DEFAULT 0'),
            ('rldl','BOOLEAN DEFAULT 0'),
            ('rlup','BOOLEAN DEFAULT 0'),
            ('mngweb','BOOLEAN DEFAULT 0'),
            ('prune','BOOLEAN DEFAULT 0')
            ]

            for column_name ,column_def in columns_to_add :
                if column_name not in existing_columns :
                    try :
                        await db .execute (f'ALTER TABLE whitelisted_users ADD COLUMN {column_name} {column_def}')
                        print (f"Added missing column: {column_name}")
                    except Exception as e :
                        print (f"Failed to add column {column_name}: {e}")

            await db .commit ()
            print ("Database migration completed successfully")
    except Exception as e :
        print (f"Database migration error: {e}")


try :
    import asyncio 
    asyncio .create_task (migrate_whitelist_table ())
except RuntimeError :

    pass 

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
