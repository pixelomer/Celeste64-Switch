using System;
using System.Numerics;
using SharpGLTF.Animations;

namespace SharpGLTF.Runtime;

// Keys are immutable, shared by instances; lookup has no per-player cursor.
// Keep the exact pinned Core Lerp/Slerp calls and range arithmetic. Empty,
// singleton, nonfinite/unsorted keys and NaN offsets retain Core behavior.
public static class IndexedCurves
{
    private static bool Supported<T>((float Key, T Value)[] keys)
    {
        if (keys.Length < 2) return false;
        for (int i=0;i<keys.Length;i++)
            if (!float.IsFinite(keys[i].Key) || (i>0 && !(keys[i-1].Key < keys[i].Key))) return false;
        return true;
    }

    private static void Range<T>((float Key,T Value)[] keys, float offset, out int left, out int right, out float amount)
    {
        if (offset < keys[0].Key) offset=keys[0].Key;
        int lo=0,hi=keys.Length;
        // Upper bound: exact-key sampling uses that key and the following key.
        while (lo<hi)
        {
            int mid=lo+((hi-lo)>>1);
            if (keys[mid].Key <= offset) lo=mid+1; else hi=mid;
        }
        left=lo-1;
        right=lo<keys.Length ? lo : left;
        amount=left==right ? 0 : (offset-keys[left].Key)/(keys[right].Key-keys[left].Key);
    }

    public static ICurveSampler<Vector3> Create((float Key,Vector3 Value)[] keys,bool linear)
    {
        var original=keys.CreateSampler(isLinear:linear,optimize:false);
        return Supported(keys) ? new VectorCurve(keys,linear,original) : original;
    }
    public static ICurveSampler<Quaternion> Create((float Key,Quaternion Value)[] keys,bool linear)
    {
        var original=keys.CreateSampler(isLinear:linear,optimize:false);
        return Supported(keys) ? new QuaternionCurve(keys,linear,original) : original;
    }
    private sealed class VectorCurve : ICurveSampler<Vector3>
    {
        private readonly (float Key,Vector3 Value)[] keys;
        private readonly bool linear;
        private readonly ICurveSampler<Vector3> original;
        public VectorCurve((float,Vector3)[] keys,bool linear,ICurveSampler<Vector3> original)
        {this.keys=keys;this.linear=linear;this.original=original;}
        public int MaxDegree => linear ? 1 : 0;
        public Vector3 GetPoint(float offset)
        {
            if (float.IsNaN(offset)) return original.GetPoint(offset);
            Range(keys,offset,out int a,out int b,out float t);
            return linear ? Vector3.Lerp(keys[a].Value,keys[b].Value,t) : keys[a].Value;
        }
    }
    private sealed class QuaternionCurve : ICurveSampler<Quaternion>
    {
        private readonly (float Key,Quaternion Value)[] keys;
        private readonly bool linear;
        private readonly ICurveSampler<Quaternion> original;
        public QuaternionCurve((float,Quaternion)[] keys,bool linear,ICurveSampler<Quaternion> original)
        {this.keys=keys;this.linear=linear;this.original=original;}
        public int MaxDegree => linear ? 1 : 0;
        public Quaternion GetPoint(float offset)
        {
            if (float.IsNaN(offset)) return original.GetPoint(offset);
            Range(keys,offset,out int a,out int b,out float t);
            return linear ? Quaternion.Slerp(keys[a].Value,keys[b].Value,t) : keys[a].Value;
        }
    }
}
