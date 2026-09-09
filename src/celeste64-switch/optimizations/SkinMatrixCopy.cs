using System;
using System.Collections.Generic;
using System.Numerics;
using System.Runtime.InteropServices;
namespace Celeste64;
public static unsafe class SkinMatrixCopy
{
    [DllImport("FosterPlatform",CallingConvention=CallingConvention.Cdecl)]
    private static extern void FosterCopySkinMatrices(Matrix4x4* destination,Matrix4x4* source,int count);
    public static void Copy(IReadOnlyList<Matrix4x4> source,Matrix4x4[] destination)
    {
        int count=Math.Min(destination.Length,source.Count);
        if(source is Matrix4x4[] contiguous)
        {
            fixed(Matrix4x4* src=contiguous)
            fixed(Matrix4x4* dst=destination)
                FosterCopySkinMatrices(dst,src,count);
        }
        else for(int j=0;j<count;j++)destination[j]=source[j];
    }
}
