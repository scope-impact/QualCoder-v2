/**
 * Projects Context: Settings Functions
 *
 * Query and mutation functions for project settings.
 */

import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

// =========================================================================
// Queries
// =========================================================================

export const get = query({
  args: { key: v.string() },
  handler: async (ctx, args) => {
    const settings = await ctx.db
      .query("prj_settings")
      .withIndex("by_key", (q) => q.eq("key", args.key))
      .first();
    return settings?.value ?? null;
  },
});

export const getAll = query({
  args: {},
  handler: async (ctx) => {
    const settings = await ctx.db.query("prj_settings").collect();
    const result: Record<string, string | null> = {};
    for (const setting of settings) {
      result[setting.key] = setting.value ?? null;
    }
    return result;
  },
});

// =========================================================================
// Mutations
// =========================================================================

export const set = mutation({
  args: {
    key: v.string(),
    value: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("prj_settings")
      .withIndex("by_key", (q) => q.eq("key", args.key))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        value: args.value,
        updated_at: new Date().toISOString(),
      });
    } else {
      await ctx.db.insert("prj_settings", {
        key: args.key,
        value: args.value,
        updated_at: new Date().toISOString(),
      });
    }
  },
});

export const remove = mutation({
  args: { key: v.string() },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("prj_settings")
      .withIndex("by_key", (q) => q.eq("key", args.key))
      .first();

    if (existing) {
      await ctx.db.delete(existing._id);
    }
  },
});

// =========================================================================
// Convenience Functions
// =========================================================================

export const getProjectName = query({
  args: {},
  handler: async (ctx) => {
    const setting = await ctx.db
      .query("prj_settings")
      .withIndex("by_key", (q) => q.eq("key", "project_name"))
      .first();
    return setting?.value ?? null;
  },
});

export const setProjectName = mutation({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("prj_settings")
      .withIndex("by_key", (q) => q.eq("key", "project_name"))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        value: args.name,
        updated_at: new Date().toISOString(),
      });
    } else {
      await ctx.db.insert("prj_settings", {
        key: "project_name",
        value: args.name,
        updated_at: new Date().toISOString(),
      });
    }
  },
});
